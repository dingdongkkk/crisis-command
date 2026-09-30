"""Synthetic, revocable Medical ID data, separately stored from immutable audit events."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import Field

from app.api.routes import (
    OPERATOR,
    PROBLEM_RESPONSES,
    IdempotencyKey,
    _require_key,
    _result_response,
    _store,
)
from app.contracts.commands import MedicalProfileAccessCommand, SessionBound
from app.contracts.common import Id
from app.contracts.events import MedicalProfileAccessPayload
from app.contracts.state import StateSnapshot
from app.domain.commands import DomainError
from app.planning.service import event
from app.storage.event_store import Decision, problem

router = APIRouter()
FIELDS = ("conditions", "medications", "allergies", "emergency_contacts")


class ProfileWrite(SessionBound):
    consent_granted: bool
    scope: list[str]
    # The incident the (synthetic) caller shared this Medical ID for; access is per incident.
    linked_incident_id: Id | None = None
    conditions: list[str] = Field(default_factory=list, max_length=20)
    medications: list[str] = Field(default_factory=list, max_length=20)
    allergies: list[str] = Field(default_factory=list, max_length=20)
    emergency_contacts: list[str] = Field(default_factory=list, max_length=5)
    synthetic: bool = True


def denial_reason(
    state: StateSnapshot, incident_id: str, profile: dict[str, Any] | None, operator_reason: str
) -> str | None:
    """First failing 0008 access rule, or None when every rule holds.

    ``caller_is_patient`` is a triage fact; missing or ``unknown`` denies (0008).
    """
    if not operator_reason.strip():
        return "MISSING_OPERATOR_REASON"
    if not any(i.incident_id == incident_id and i.status == "active" for i in state.incidents):
        return "INCIDENT_NOT_ACTIVE"
    if profile is None or profile.get("linked_incident_id") != incident_id:
        return "PROFILE_NOT_LINKED"
    if not profile["consent_granted"]:
        return "CONSENT_REVOKED" if profile.get("consent_revoked") else "NO_CONSENT"
    facts = next((f for f in state.triage_facts if f.incident_id == incident_id), None)
    fact = next((f for f in facts.facts if f.key == "caller_is_patient"), None) if facts else None
    value = fact.value if fact else None
    if value == "no":
        return "CALLER_IS_NOT_PATIENT"
    if value != "yes":
        return "CALLER_IS_PATIENT_UNKNOWN"
    return None


def denied(reason: str) -> dict[str, Any]:
    body = problem(DomainError(403, "PROFILE_ACCESS_DENIED", "Medical profile access denied"))
    body["reason"] = reason
    return body


def profile_data(request: Request, ref: str) -> dict[str, Any] | None:
    # All profile mutations use the same EventStore write transaction as access decisions.
    with sqlite3.connect(_store(request).path) as conn:
        row = conn.execute("SELECT data FROM profiles WHERE profile_ref=?", (ref,)).fetchone()
    return json.loads(row[0]) if row else None


@router.put("/medical-profiles/{profile_ref}", responses=PROBLEM_RESPONSES)
def put_profile(
    request: Request,
    profile_ref: str,
    command: ProfileWrite,
    idempotency_key: IdempotencyKey = None,
) -> JSONResponse:
    def decide(_: StateSnapshot) -> Decision:
        if not command.synthetic or set(command.scope) - set(FIELDS):
            raise DomainError(
                422, "VALIDATION_FAILED", "Synthetic profiles and supported consent scopes only"
            )
        data = command.model_dump(exclude={"expected_session_id"})
        previous = profile_data(request, profile_ref)
        if not command.consent_granted:
            for field in FIELDS:
                data[field] = []
            data["consent_revoked"] = bool(
                previous and (previous["consent_granted"] or previous.get("consent_revoked"))
            )

        def write(conn: sqlite3.Connection) -> None:
            conn.execute(
                "INSERT INTO profiles VALUES (?, ?) ON CONFLICT(profile_ref) "
                "DO UPDATE SET data=excluded.data",
                (profile_ref, json.dumps(data)),
            )

        return Decision(
            [],
            lambda _: (
                200,
                {"profile_ref": profile_ref, "consent_granted": command.consent_granted},
            ),
            write,
        )

    return _result_response(
        _store(request).execute(
            method="PUT",
            path=f"/medical-profiles/{profile_ref}",
            key=_require_key(idempotency_key),
            body=command.model_dump(mode="json"),
            expected_session_id=command.expected_session_id,
            decide=decide,
            actor=OPERATOR,
        )
    )


@router.post("/incidents/{incident_id}/medical-profile-access", responses=PROBLEM_RESPONSES)
def access_profile(
    request: Request,
    incident_id: str,
    command: MedicalProfileAccessCommand,
    idempotency_key: IdempotencyKey = None,
) -> JSONResponse:
    # Never persist values in a command receipt: the receipt holds only authorized field names.
    def decide(state: StateSnapshot) -> Decision:
        profile = profile_data(request, command.profile_ref)
        reason = denial_reason(state, incident_id, profile, command.operator_reason)
        fields = [f for f in FIELDS if profile and f in profile["scope"]] if reason is None else []
        audit = MedicalProfileAccessPayload.model_validate(
            dict(
                incident_id=incident_id,
                profile_ref=command.profile_ref,
                granted_fields=fields,
                reason=reason,
            )
        )
        return Decision(
            [
                event(
                    state,
                    "MedicalProfileAccessDenied" if reason else "MedicalProfileAccessGranted",
                    audit,
                    "incident",
                    incident_id,
                )
            ],
            lambda _: (
                (403, denied(reason))
                if reason
                else (200, {"profile_ref": command.profile_ref, "granted_fields": fields})
            ),
        )

    result = _store(request).execute(
        method="POST",
        path=f"/incidents/{incident_id}/medical-profile-access",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=decide,
        actor=OPERATOR,
    )
    if result.status != 200:
        return _result_response(result)
    # Bind the fresh authorization and value read to one SQLite writer transaction: a replayed
    # receipt never returns values unless every rule still holds now (revocation wins).
    store = _store(request)
    with store.private_read() as (conn, current):
        row = conn.execute(
            "SELECT data FROM profiles WHERE profile_ref=?", (command.profile_ref,)
        ).fetchone()
        profile = json.loads(row[0]) if row else None
        reason = (
            "INCIDENT_NOT_ACTIVE"
            if current.session_id != command.expected_session_id
            else denial_reason(current, incident_id, profile, command.operator_reason)
        )
        if reason or profile is None:
            return JSONResponse(denied(reason or "PROFILE_NOT_LINKED"), status_code=403)
        fields = [f for f in result.body["granted_fields"] if f in profile["scope"]]
        values = {f: profile[f] for f in fields}
    return JSONResponse(
        {"profile_ref": command.profile_ref, "values": values},
        headers={"Cache-Control": "no-store"},
    )
