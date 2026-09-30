#!/usr/bin/env bash
# Start the Crisis Command demo: backend API + operator console, both on localhost.
# Synthetic data and simulated dispatch only. No API keys, no network needed after install.
#
#   scripts/demo.sh            # persistent database backend/data/crisis.db
#   scripts/demo.sh --fresh    # new empty database under backend/data/ (old ones are kept)
#
# Ports: BACKEND_PORT (default 8321) and CONSOLE_PORT (default 5321). Ctrl-C stops both.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_PORT="${BACKEND_PORT:-8321}"
CONSOLE_PORT="${CONSOLE_PORT:-5321}"
DATABASE_PATH="${DATABASE_PATH:-$ROOT/backend/data/crisis.db}"
if [[ "${1:-}" == "--fresh" ]]; then
  DATABASE_PATH="$ROOT/backend/data/crisis-$(date +%Y%m%d-%H%M%S).db"
fi

need() { command -v "$1" >/dev/null 2>&1 || { echo "Missing $1. $2" >&2; exit 1; }; }
need uv "Install uv: https://docs.astral.sh/uv/getting-started/installation/"
need node "Install Node.js 22 or newer: https://nodejs.org/"
need npm "npm ships with Node.js."
node_major="$(node -p 'process.versions.node.split(".")[0]')"
if (( node_major < 22 )); then echo "Node.js 22+ required (found $(node --version))." >&2; exit 1; fi
for port in "$BACKEND_PORT" "$CONSOLE_PORT"; do
  if lsof -iTCP:"$port" -sTCP:LISTEN >/dev/null 2>&1; then
    echo "Port $port is in use. Set BACKEND_PORT / CONSOLE_PORT to free ports." >&2
    exit 1
  fi
done

echo "Installing locked dependencies (first run only takes a minute)…"
(cd "$ROOT/backend" && uv sync --frozen --quiet)
[[ -d "$ROOT/frontend/node_modules" ]] || (cd "$ROOT/frontend" && npm ci --no-audit --no-fund --loglevel=error)

pids=()
cleanup() { for pid in "${pids[@]}"; do kill "$pid" 2>/dev/null || true; done; }
trap cleanup EXIT INT TERM

echo "Backend  → http://127.0.0.1:$BACKEND_PORT  (database: $DATABASE_PATH)"
(cd "$ROOT/backend" && DATABASE_PATH="$DATABASE_PATH" exec uv run uvicorn app.main:app \
  --host 127.0.0.1 --port "$BACKEND_PORT" --log-level warning) &
pids+=($!)

for _ in $(seq 1 60); do
  curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null 2>&1 && break
  sleep 0.5
done
curl -fsS "http://127.0.0.1:$BACKEND_PORT/health" >/dev/null || { echo "Backend did not start." >&2; exit 1; }

(cd "$ROOT/frontend" && CRISIS_BACKEND_URL="http://127.0.0.1:$BACKEND_PORT" exec npm run dev --silent -- \
  --host 127.0.0.1 --port "$CONSOLE_PORT" --strictPort) &
pids+=($!)

cat <<EOF

  Operator console  http://127.0.0.1:$CONSOLE_PORT
  API docs          http://127.0.0.1:$BACKEND_PORT/docs
  Mock-only console http://127.0.0.1:$CONSOLE_PORT/?mock=demo

  SIMULATION ONLY — synthetic data, simulated dispatch. Press Ctrl-C to stop.

EOF
wait
