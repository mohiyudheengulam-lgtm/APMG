# Procurement Verification Agent

University engineering project at THWS comparing Standard Retrieval-Augmented Generation (RAG) with the Open Knowledge Format (OKF) for procurement compliance verification.

The system is designed around small local language models under 2B parameters, run through Ollama. Keeping inference and project data local supports absolute data privacy and makes the approach suitable for sensitive procurement documents.

## Problem Statement (WIP)

The final problem statement is currently being drafted. This section will define the procurement verification use case, the compliance questions to be answered, the boundaries of the agent's decisions, and the measurable research questions for comparing Standard RAG with OKF.

## Team Structure

The project is divided into three coordinated modules:

1. **Module 1 - Data Pipeline** (`data_pipeline/`)
	Document parsing, indexing, retrieval preparation, and conversion of structured and unstructured sources into OKF Markdown bundles.
2. **Module 2 - Agentic Engine** (`agentic_engine/`)
	ReAct reasoning, tool definitions, local model orchestration, and controlled procurement status updates.
3. **Module 3 - Frontend UI** (`frontend_ui/`)
	Web and chatbot experience for document uploads, verification requests, results, and user interaction.

Project planning, research, and evaluation material belongs in [`docs/`](docs/).

## Privacy and Local Development

Run language models locally with [Ollama](https://ollama.com/). Do not commit credentials, downloaded model artifacts, vector databases, test outputs, or procurement documents. The repository's `.gitignore` contains the baseline protections for local development.

## Status

This repository currently contains the project skeleton. Module-specific implementation details and the formal evaluation plan will be added as the problem statement is finalized.

## Prototype: Agent On Duty (working system)

A complete working prototype lives in this repository root (`src/`, `scripts/`, `web/`, `tests/`).
It follows the revised exposé (`docs/expose.md`): Qwen3-1.7B via Ollama, Path A = FAISS vector RAG,
Path B = OKF v0.2 bundles, plain-Python ReAct agent, SQLite + JSON audit, human approval gate, Next.js UI.
Start with `CONTEXT.md`, `SETUP.md` and the visual walkthrough `docs/system-overview.html`.

Local agentic procurement verification — see `CONTEXT.md` and `docs/expose.md`.

```bash
uv sync                      # install deps
uv run pytest                # tests
ollama pull qwen3:1.7b && ollama pull nomic-embed-text
brew install tesseract       # OCR fallback only
```

**Download:** every version tag builds the installer on GitHub — see the repository's *Releases* page
(`agent_on_duty-<version>-py3-none-any.whl`). Then `uv tool install <file>.whl` and `agent-on-duty --demo`.

Install as a single program (API + web app in one process, any OS with Python 3.12 and Ollama):

```bash
scripts/build_app.sh                                   # builds dist/agent_on_duty-0.1.0-py3-none-any.whl
uv tool install dist/agent_on_duty-0.1.0-py3-none-any.whl
agent-on-duty                                          # opens http://localhost:8000 ; data in ~/AgentOnDuty
```
(`--host 0.0.0.0` makes it reachable from other devices on the network; `AOD_HOME` changes the data folder.)

Development (hot reload — API on :8000, UI on http://localhost:3100):

```bash
scripts/dev.sh            # or separately:
uv run uvicorn agent_on_duty.api:app --port 8000
cd web && npm install && npx next dev -p 3100
```

Benchmark: `uv run python scripts/run_benchmark.py --tag full` then `uv run python scripts/evaluate.py --tag full`.
The legacy Streamlit UI (`src/agent_on_duty/ui/app.py`) is superseded by `web/`.

Layout: `src/agent_on_duty/{schemas.py, tools/, extraction/, retrieval/, agent/, audit/, ui/}`,
`scripts/` (dataset generator, OKF converter, eval), `data/seeds` (templates), `data/packages` (generated benchmark).
