"""Live intake wiring: optional model call outside the write lock and model health.

``prefetch`` runs before the event-store transaction. Every failure (timeout, transport,
invalid output, unexpected exception) becomes a recorded ``ModelUnavailableError`` cause, so
the rules-only path always completes and escalation never waits on the model (0002).
"""

from __future__ import annotations

import threading

from .model_adapter import (
    DEFAULT_TIMEOUT_S,
    FactModel,
    GeminiAdapter,
    ModelUnavailableError,
    RecordedModel,
)
from .rules import extract


class IntakeService:
    def __init__(
        self, model: FactModel | None, *, configured: bool, timeout_s: float = DEFAULT_TIMEOUT_S
    ) -> None:
        self.model = model
        self.configured = configured  # a model provider was requested in settings
        self.timeout_s = timeout_s
        self._lock = threading.Lock()
        self._last_failure: str | None = None if model or not configured else "NO_API_KEY"

    @classmethod
    def from_settings(cls, llm_provider: str) -> IntakeService:
        if llm_provider != "gemini":
            return cls(None, configured=False)
        return cls(GeminiAdapter.from_env(), configured=True)

    def prefetch(self, text: str) -> RecordedModel | None:
        """Model outcome for ``text``, or None when no model is configured."""
        if not self.configured:
            return None
        if self.model is None:
            return RecordedModel(None, "NO_API_KEY")
        if extract(text).injection_suspected:
            # The session discards model output for suspected injection; do not send it at all.
            return RecordedModel(None, "PROMPT_INJECTION_SUSPECTED")
        try:
            extraction = self.model.extract(text, timeout_s=self.timeout_s)
        except ModelUnavailableError as exc:
            self._record(exc.cause)
            return RecordedModel(None, exc.cause)
        except Exception:  # any adapter defect degrades to rules-only
            self._record("ADAPTER_ERROR")
            return RecordedModel(None, "ADAPTER_ERROR")
        self._record(None)
        return RecordedModel(extraction)

    def _record(self, failure: str | None) -> None:
        with self._lock:
            self._last_failure = failure

    @property
    def degraded(self) -> list[str]:
        with self._lock:
            return ["MODEL_UNAVAILABLE"] if self.configured and self._last_failure else []

    @property
    def last_failure(self) -> str | None:
        with self._lock:
            return self._last_failure
