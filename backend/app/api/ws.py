"""WebSocket ``/ws/events``: hello, subscribe, backlog, caught_up, live events, heartbeat (0005).

A subscription registers for live events *before* reading the backlog, then drops
duplicates by sequence, so no event can fall into the gap between the two. A session
change (demo reset) ends the subscription with ``snapshot_required``.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.contracts.commands import WsSubscribe
from app.contracts.common import SCHEMA_VERSION
from app.contracts.events import EnvelopeBase
from app.storage.event_store import EventStore

router = APIRouter()


class _Subscriber:
    """Bridges store commits (worker threads) into one connection's event loop."""

    def __init__(self, store: EventStore) -> None:
        self.loop = asyncio.get_running_loop()
        self.queue: asyncio.Queue[EnvelopeBase] = asyncio.Queue()
        self._unsubscribe = store.subscribe(self._on_commit)

    def _on_commit(self, events: list[EnvelopeBase]) -> None:
        for event in events:
            self.loop.call_soon_threadsafe(self.queue.put_nowait, event)

    def close(self) -> None:
        self._unsubscribe()


def _event_message(event: EnvelopeBase) -> dict[str, Any]:
    return {"type": "event", "event": event.model_dump(mode="json", by_alias=True)}


async def _next_subscribe(ws: WebSocket) -> WsSubscribe:
    while True:
        message = await ws.receive_json()
        try:
            return WsSubscribe.model_validate(message)
        except ValidationError:
            await ws.send_json({"type": "error", "code": "VALIDATION_FAILED"})


@router.websocket("/ws/events")
async def events_socket(ws: WebSocket) -> None:
    store: EventStore = ws.app.state.store
    heartbeat_s: float = ws.app.state.heartbeat_s
    await ws.accept()
    subscriber = _Subscriber(store)
    try:
        active = store.active_session() or ""
        await ws.send_json(
            {
                "type": "hello",
                "session_id": active,
                "head_sequence": store.head_sequence(active),
                "schema_version": SCHEMA_VERSION,
            }
        )
        subscription = await _next_subscribe(ws)
        while True:
            subscription = await _stream(ws, store, subscriber, subscription, heartbeat_s)
    except WebSocketDisconnect:
        pass
    finally:
        subscriber.close()


async def _stream(
    ws: WebSocket,
    store: EventStore,
    subscriber: _Subscriber,
    subscription: WsSubscribe,
    heartbeat_s: float,
) -> WsSubscribe:
    """Serve one subscription; return the next subscribe message when it ends."""
    session = subscription.session_id
    active = store.active_session() or ""
    head = store.head_sequence(active)
    if session != active or subscription.after_sequence > head:
        await ws.send_json({"type": "snapshot_required", "session_id": active})
        return await _next_subscribe(ws)

    last = subscription.after_sequence
    for event in await asyncio.to_thread(store.events, session, last):
        await ws.send_json(_event_message(event))
        last = event.sequence
    await ws.send_json({"type": "caught_up", "head_sequence": last})

    receive = asyncio.create_task(_next_subscribe(ws))
    try:
        while True:
            get = asyncio.create_task(subscriber.queue.get())
            done, _ = await asyncio.wait(
                {get, receive}, timeout=heartbeat_s, return_when=asyncio.FIRST_COMPLETED
            )
            if receive in done:
                get.cancel()
                return receive.result()
            if get not in done:
                get.cancel()
                await ws.send_json({"type": "heartbeat", "head_sequence": last})
                continue
            event = get.result()
            if event.session_id != session:
                if event.session_id == store.active_session():
                    await ws.send_json(
                        {"type": "snapshot_required", "session_id": event.session_id}
                    )
                    return await receive
                continue  # late event for a closed session (e.g. reset cancellations)
            if event.sequence <= last:
                continue  # already delivered in the backlog
            await ws.send_json(_event_message(event))
            last = event.sequence
    finally:
        if not receive.done():
            receive.cancel()
            with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
                await receive
