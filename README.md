# Agent On Duty (APMG)

Local agentic procurement verification — see `CONTEXT.md` and `docs/expose.md`.

```bash
uv sync                      # install deps
uv run pytest                # tests
ollama pull qwen3:1.7b && ollama pull nomic-embed-text
brew install tesseract       # OCR fallback only
```

Run the app (API on :8000, UI on http://localhost:3100):

```bash
scripts/dev.sh            # or separately:
uv run uvicorn agent_on_duty.api:app --port 8000
cd web && npm install && npx next dev -p 3100
```

Benchmark: `uv run python scripts/run_benchmark.py --tag full` then `uv run python scripts/evaluate.py --tag full`.
The legacy Streamlit UI (`src/agent_on_duty/ui/app.py`) is superseded by `web/`.

Layout: `src/agent_on_duty/{schemas.py, tools/, extraction/, retrieval/, agent/, audit/, ui/}`,
`scripts/` (dataset generator, OKF converter, eval), `data/seeds` (templates), `data/packages` (generated benchmark).
