"""Pure projection against the CC-01 golden fixtures (checkpoint 52 + suffix 53-67)."""

from __future__ import annotations

import pytest

from app.contracts import EVENT_ADAPTER
from app.contracts.events import EnvelopeBase
from app.contracts.state import StateSnapshot
from app.domain.projection import ProjectionError, apply, fold, state_hash
from tests.fixtures import load

CHECKPOINT = StateSnapshot.model_validate(load("world.before.json"))
EVENTS: list[EnvelopeBase] = [EVENT_ADAPTER.validate_python(e) for e in load("events.valid.json")]


def test_fold_reproduces_the_seq_60_snapshot_example() -> None:
    snapshot = next(c for c in load("api.examples.json") if c["name"] == "state_snapshot")
    expected = StateSnapshot.model_validate(snapshot["response"]["body"])
    assert fold([e for e in EVENTS if e.sequence <= 60], CHECKPOINT) == expected


def test_full_suffix_ends_dispatched_with_planning_sequence_67() -> None:
    state = fold(EVENTS, CHECKPOINT)
    assert (state.as_of_sequence, state.planning_sequence) == (67, 67)
    assert state.current_proposal is None
    assert state.approved_plan is not None and state.approved_plan.plan_id == "plan_0007"
    assert state.approved_plan.state == "dispatched_simulated"
    assert {c.state for c in state.outbox} == {"sent"}
    b2 = next(u for u in state.units if u.unit_id == "unit_B2")
    assert b2.status == "en_route" and b2.current_task is not None


def test_non_planning_events_do_not_move_planning_sequence() -> None:
    state = fold([e for e in EVENTS if e.sequence <= 60], CHECKPOINT)
    assert state.planning_sequence == 58  # 59 PlanProposed and 60 OverrideRejected are audit-only


def test_snapshot_plus_suffix_equals_single_fold() -> None:
    mid = fold([e for e in EVENTS if e.sequence <= 61], CHECKPOINT)
    assert state_hash(fold([e for e in EVENTS if e.sequence > 61], mid)) == state_hash(
        fold(EVENTS, CHECKPOINT)
    )


def test_gap_and_wrong_session_are_rejected() -> None:
    with pytest.raises(ProjectionError, match="gap"):
        apply(CHECKPOINT, EVENTS[1])
    other = EVENTS[0].model_copy(update={"session_id": "sess_other"})
    with pytest.raises(ProjectionError, match="different session"):
        apply(CHECKPOINT, other)


def test_log_must_start_with_session_started() -> None:
    with pytest.raises(ProjectionError):
        apply(None, EVENTS[0])


def test_approval_must_match_current_proposal() -> None:
    before_approval = fold([e for e in EVENTS if e.sequence <= 60], CHECKPOINT)
    no_proposal = before_approval.model_copy(update={"current_proposal": None})
    with pytest.raises(ProjectionError, match="approval"):
        apply(no_proposal, next(e for e in EVENTS if e.sequence == 61))
