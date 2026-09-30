import pytest
from fastapi.testclient import TestClient

from app.config import ConfigError, Settings
from app.contracts import SCHEMA_VERSION
from app.contracts.commands import HealthResponse
from app.main import create_app
from tests.fixtures import load


def test_health_matches_contract_example() -> None:
    response = TestClient(create_app()).get("/health")
    assert response.status_code == 200
    assert HealthResponse.model_validate(response.json()).schema_version == SCHEMA_VERSION
    example = next(c for c in load("api.examples.json") if c["name"] == "health")
    assert response.json() == example["response"]["body"]


def test_only_simulation_mode_exists(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CRISIS_MODE", "live")
    with pytest.raises(ConfigError):
        Settings.from_env()
