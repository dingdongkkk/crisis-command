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
