"""Synthetic, revocable Medical ID data, separately stored from immutable audit events."""

from __future__ import annotations

import json
import sqlite3
from typing import Annotated, Any

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
from app.contracts.commands import SessionBound
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
    conditions: list[str] = Field(default_factory=list, max_length=20)
    medications: list[str] = Field(default_factory=list, max_length=20)
    allergies: list[str] = Field(default_factory=list, max_length=20)
    emergency_contacts: list[str] = Field(default_factory=list, max_length=5)
    synthetic: bool = True


class ProfileRead(SessionBound):
    profile_ref: Id
    caller_is_patient: bool
    operator_reason: Annotated[str, Field(min_length=1, max_length=280)]


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
        if not command.consent_granted:
            for field in FIELDS:
                data[field] = []

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


@router.post("/incidents/{incident_id}/medical-profile/access", responses=PROBLEM_RESPONSES)
def access_profile(
    request: Request, incident_id: str, command: ProfileRead, idempotency_key: IdempotencyKey = None
) -> JSONResponse:
    # Never persist values in a command receipt: the receipt holds only authorized field names.
    def decide(state: StateSnapshot) -> Decision:
        profile = profile_data(request, command.profile_ref)
        active = any(i.incident_id == incident_id and i.status == "active" for i in state.incidents)
        granted = bool(
            active and command.caller_is_patient and profile and profile["consent_granted"]
        )
        fields = [f for f in FIELDS if profile and f in profile["scope"]] if granted else []
        audit = MedicalProfileAccessPayload.model_validate(
            dict(
                incident_id=incident_id,
                profile_ref=command.profile_ref,
                granted_fields=fields,
                reason=None if granted else "ACCESS_DENIED",
            )
        )
        error = DomainError(
            403, "ACCESS_DENIED", "Consent, caller-is-patient and active incident are required"
        )
        return Decision(
            [
                event(
                    state,
                    "MedicalProfileAccessGranted" if granted else "MedicalProfileAccessDenied",
                    audit,
                    "incident",
                    incident_id,
                )
            ],
            lambda _: (
                (200, {"profile_ref": command.profile_ref, "granted_fields": fields})
                if granted
                else (403, problem(error))
            ),
        )

    result = _store(request).execute(
        method="POST",
        path=f"/incidents/{incident_id}/medical-profile/access",
        key=_require_key(idempotency_key),
        body=command.model_dump(mode="json"),
        expected_session_id=command.expected_session_id,
        decide=decide,
        actor=OPERATOR,
    )
    if result.status != 200:
        return _result_response(result)
    # Bind the fresh authorization and value read to one SQLite writer transaction.
    store = _store(request)
    with store.private_read() as (conn, current):
        row = conn.execute(
            "SELECT data FROM profiles WHERE profile_ref=?", (command.profile_ref,)
        ).fetchone()
        profile = json.loads(row[0]) if row else None
        if (
            current.session_id != command.expected_session_id
            or not profile
            or not profile["consent_granted"]
            or not any(
                i.incident_id == incident_id and i.status == "active" for i in current.incidents
            )
        ):
            raise DomainError(403, "ACCESS_DENIED", "Access no longer valid")
        fields = [f for f in result.body["granted_fields"] if f in profile["scope"]]
        values = {f: profile[f] for f in fields}
    return JSONResponse(
        {"profile_ref": command.profile_ref, "values": values},
        headers={"Cache-Control": "no-store"},
    )
