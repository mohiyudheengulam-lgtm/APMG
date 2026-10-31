# Agent On Duty (APMG)

Local agentic procurement verification — see `CONTEXT.md` and `docs/expose.md`.

```bash
uv sync                      # install deps
uv run pytest                # tests
ollama pull qwen3:1.7b && ollama pull nomic-embed-text
brew install tesseract       # OCR fallback only
```

Layout: `src/agent_on_duty/{schemas.py, tools/, extraction/, retrieval/, agent/, audit/, ui/}`,
`scripts/` (dataset generator, OKF converter, eval), `data/seeds` (templates), `data/packages` (generated benchmark).
