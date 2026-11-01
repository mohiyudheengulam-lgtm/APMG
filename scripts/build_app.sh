#!/usr/bin/env bash
# Build the single-process app: static web UI + demo data bundled into the Python package, then a wheel in dist/.
#   scripts/build_app.sh
#   uv tool install dist/agent_on_duty-*.whl      # then run:  agent-on-duty   (or: agent-on-duty --demo)
set -e
cd "$(dirname "$0")/.."
(cd web && (npm ci --silent || npm install --silent))
(cd web && AOD_EXPORT=1 npx next build)
rm -rf src/agent_on_duty/webui && cp -R web/out src/agent_on_duty/webui

# demo data: the 24 benchmark packages + contract library (generated from the committed seed packages if missing)
ls -d data/packages/PKG-* >/dev/null 2>&1 || uv run python scripts/dataset_generator.py
uv run python - <<'PY'
import json, zipfile
from pathlib import Path
out = Path("src/agent_on_duty/demo_data.zip")
with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
    for f in sorted(Path("data/packages").glob("PKG-*/*")):
        if f.suffix in (".pdf", ".json"):
            z.write(f, f"packages/{f.parent.name}/{f.name}")
    for f in sorted(Path("data/contracts").glob("*/*")):
        if f.suffix == ".pdf":
            z.write(f, f"contracts/{f.parent.name}/{f.name}")
        elif f.name == "contract.json":  # indexes are rebuilt on the new device
            z.writestr(f"contracts/{f.parent.name}/{f.name}", json.dumps(json.loads(f.read_text()) | {"build": {}}, indent=1))
print(f"demo data: {out} ({out.stat().st_size // 1024} KB)")
PY
rm -rf dist && uv build --wheel
ls -lh dist/
