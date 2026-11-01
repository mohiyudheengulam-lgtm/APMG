#!/usr/bin/env bash
# Build the single-process app: static web UI bundled into the Python package, then a wheel in dist/.
#   scripts/build_app.sh
#   uv tool install dist/agent_on_duty-*.whl      # then run:  agent-on-duty
set -e
cd "$(dirname "$0")/.."
(cd web && npm install --silent && AOD_EXPORT=1 npx next build)
rm -rf src/agent_on_duty/webui && cp -R web/out src/agent_on_duty/webui
rm -rf dist && uv build --wheel
ls -lh dist/
