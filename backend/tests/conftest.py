from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.storage.event_store import EventStore


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "crisis.db"


@pytest.fixture
def store(db_path: Path) -> EventStore:
    s = EventStore(db_path)
    s.ensure_session()
    return s


@pytest.fixture
def client(store: EventStore) -> Iterator[TestClient]:
    with TestClient(create_app(store=store, heartbeat_s=0.2)) as c:
        yield c
