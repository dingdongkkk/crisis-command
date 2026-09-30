# Backend

Python 3.12, FastAPI, Pydantic v2. Dependencies are locked in `uv.lock`. Simulation mode only.

```sh
cd backend
uv sync --frozen                            # install exactly the locked versions
uv run ruff check . && uv run ruff format --check .
uv run mypy                                 # strict
uv run pytest                               # health + contract tests
uv run python -m app.contracts.export       # regenerate contracts/schema + openapi.json
uv run python -m app.contracts.export --check
uv run uvicorn app.main:app --reload        # http://127.0.0.1:8000/health
```

Install `uv` from https://docs.astral.sh/uv/ if missing. Canonical models live in
`app/contracts/`; see `contracts/README.md` for the generation chain.

## Layout and runtime behaviour (CC-03)

- `app/domain/projection.py` — pure `fold(apply, events)`; golden-tested against the CC-01 fixtures.
- `app/domain/commands.py` — pure decisions (unit status, flood versions, session start from `evals/fixtures/demo-bengaluru-v1.json`).
- `app/storage/event_store.py` — SQLite (WAL) append-only log, write-through projection, idempotency receipts that survive resets, `BEGIN IMMEDIATE` per command, 1 s busy budget → `503 DATABASE_BUSY`.
- `app/api/` — `GET /state[?at_sequence&session_id]`, `GET /events?session_id&after_sequence`, `POST /units/{id}/status`, `POST /flood-events`, `POST /demo/reset`, `WS /ws/events`.

The database defaults to `./data/crisis.db` (`DATABASE_PATH`). Deleting it is the only way to discard history and receipts; `POST /demo/reset` starts a new session in the same file.

