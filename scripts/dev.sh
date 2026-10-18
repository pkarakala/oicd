#!/usr/bin/env bash
# Start the engine API (port 8000) and the web explorer (port 5173); Ctrl+C stops both.
set -euo pipefail
# Job control puts each background job in its own process group, so Ctrl+C cleanup can stop
# the whole group (npm -> vite, uv -> uvicorn).
set -m

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

pids=()
cleanup() {
  trap - INT TERM EXIT
  for pid in "${pids[@]}"; do
    kill -TERM -- "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
  done
  wait 2>/dev/null || true
}
trap cleanup INT TERM EXIT

uv run uvicorn oicd.api:app --port 8000 &
pids+=($!)

(cd web && npm run dev) &
pids+=($!)

echo "API: http://127.0.0.1:8000  explorer: http://localhost:5173  (Ctrl+C to stop)"
# Exit (and stop the other) as soon as either process ends. Polling instead of `wait -n`
# keeps this working on macOS's bash 3.2.
while kill -0 "${pids[0]}" 2>/dev/null && kill -0 "${pids[1]}" 2>/dev/null; do
  sleep 1
done
