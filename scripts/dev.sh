#!/usr/bin/env bash
# Start the local API (port 8000) and the Next.js UI (port 3100). Ctrl-C stops both.
set -e
cd "$(dirname "$0")/.."
# keep-alive longer than the Next.js proxy reuses connections, or reused sockets get reset under load
uv run uvicorn agent_on_duty.api:app --host 127.0.0.1 --port 8000 --timeout-keep-alive 75 &
API=$!
trap 'kill $API 2>/dev/null' EXIT
cd web && npx next dev -p 3100
