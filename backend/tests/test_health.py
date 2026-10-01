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


def test_cors_only_for_listed_origins(store, monkeypatch) -> None:  # type: ignore[no-untyped-def]
    from fastapi.testclient import TestClient

    from app.main import create_app

    monkeypatch.setenv("CRISIS_CORS_ORIGINS", "https://console.example")
    with TestClient(create_app(store=store, auto_plan=False)) as client:
        ok = client.get("/health", headers={"Origin": "https://console.example"})
        assert ok.headers.get("access-control-allow-origin") == "https://console.example"
        other = client.get("/health", headers={"Origin": "https://evil.example"})
        assert "access-control-allow-origin" not in other.headers
        preflight = client.options(
            "/reports",
            headers={
                "Origin": "https://console.example",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "content-type,idempotency-key",
            },
        )
        assert preflight.status_code == 200
