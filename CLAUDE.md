# Agent On Duty — APMG Group Project

Fully local agentic AI system for procurement verification and MSA policy compliance auditing. THWS, supervised by Fahad Rafique.

## IMPORTANT — do this first, every session

Before answering anything, ask the user:

"Hi! Who are you? Pick your number:
1. Mohiyudheen Kalluparamban
2. Sara Shaban
3. Rishikta Bhore
4. Navya Gupta
5. Vijayadharshan Periyasamy
6. Allen Smith"

Once they answer, tell them their focus area (Allen=1, Sara=2, Mohi=3, Navya=4, Rishiktha=5, VD=6) and run `/whoami`. After that, help them with anything they ask — this is a group project and everyone needs to understand the whole system. Naturally emphasize their area when relevant, and mention who owns a piece of code when it helps them collaborate.

## Project structure

```
src/agent_on_duty/
  agent/react.py          ReAct loop — Qwen3-1.7B, tool calls, compaction
  retrieval/path_a.py     Path A: FAISS vector RAG (nomic-embed-text, top-5)
  retrieval/path_b.py     Path B: OKF concept navigation (read-only, no embeddings)
  extraction/             PDF extraction — PyMuPDF + Tesseract fallback
  audit/store.py          SQLite audit log + HITL gate
  api.py                  FastAPI backend (port 8000)
scripts/
  run_benchmark.py        Full benchmark runner (144 runs: 24 pkgs × 2 paths × 3 runs)
  evaluate.py             Scoring: completion rate, flag accuracy, latency
  dataset_generator.py    Synthetic procurement package generator
web/                      Next.js frontend (port 3000)
data/                     Benchmark packages (do not edit manually)
```

## Rules that never change

1. **Path A and Path B must be identical** except for the retrieval step — same model, same prompt base, same tools, same settings.
2. **HITL gate is non-negotiable** — the agent cannot write final decisions. DB constraints enforce this.
3. **Never modify `data/` packages manually** — regenerate via `scripts/dataset_generator.py`.
4. **`schemas.py` and `pyproject.toml`** require review from at least two owners before merging.
5. **Benchmark results only count** when run with `BENCHMARK_MODEL = "qwen3:1.7b"` and `--tag bench1`.

## Dev setup

```bash
# Install
uv sync

# Start backend + frontend
bash scripts/dev.sh

# Run benchmark (needs Ollama running with qwen3:1.7b and nomic-embed-text)
export OLLAMA_NUM_PARALLEL=1 OLLAMA_FLASH_ATTENTION=1 OLLAMA_KV_CACHE_TYPE=q8_0
uv run python scripts/run_benchmark.py --tag bench1 --runs 3

# Run tests
uv run pytest
```

## Git workflow

- Branch off `main`: `git checkout -b feature/<yourname>/<short-description>`
- Open a PR — CODEOWNERS will auto-assign the right reviewer
- `main` is protected: CI must pass, at least one review required
- `schemas.py` / `pyproject.toml` need two reviews
