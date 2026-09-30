"""Runtime settings from environment variables (see repository ``.env.example``)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal

Mode = Literal["simulation"]
LlmProvider = Literal["template", "gemini"]
RoutingProvider = Literal["fixture", "ors_directions"]


class ConfigError(ValueError):
    """Raised when an environment setting is outside the supported values."""


def _choice[T: str](name: str, default: T, allowed: tuple[T, ...]) -> T:
    value = os.environ.get(name, default)
    if value not in allowed:
        raise ConfigError(f"{name}={value!r} is not one of {allowed}")
    return value  # membership checked above


@dataclass(frozen=True)
class Settings:
    mode: Mode
    llm_provider: LlmProvider
    routing_provider: RoutingProvider
    database_path: str

    @classmethod
    def from_env(cls) -> Settings:
        # Only simulation mode exists: there is no configuration that enables real dispatch.
        return cls(
            mode=_choice("CRISIS_MODE", "simulation", ("simulation",)),
            llm_provider=_choice("LLM_PROVIDER", "template", ("template", "gemini")),
            routing_provider=_choice("ROUTING_PROVIDER", "fixture", ("fixture", "ors_directions")),
            database_path=os.environ.get("DATABASE_PATH", "./data/crisis.db"),
        )
