Ask the user their name, then say:

"Here are the 6 areas of the project. Read through them all — you can ask me to explain any area in depth, show you the code, or walk you through how it fits into the system. Once you've had a look, let Mohiyudheen know which area you'd like to own."

Then show this:

---

## Area 1 — Evaluation & Integration
**Report section:** §6 Research Methodology & Evaluation Framework

This is the glue of the whole project. Runs the full benchmark (144 verifications: 24 packages × 2 retrieval paths × 3 runs), scores the results against ground truth, and measures flag accuracy, latency, and token efficiency. Also owns the FastAPI backend that connects the agent to the UI.

**Key files:**
- `scripts/run_benchmark.py` — benchmark runner
- `scripts/evaluate.py` — scoring: flag precision/recall/F1, field exact match, latency
- `src/agent_on_duty/api.py` — FastAPI backend (port 8000)
- `src/agent_on_duty/benchmark/` — benchmark data models

---

## Area 2 — Document Extraction & Pipeline Architecture
**Report section:** §5 System Architecture

Handles getting information out of PDFs — purchase orders, invoices, goods receipts, and MSAs. Uses PyMuPDF with Tesseract OCR as a fallback for scanned documents. Also owns the 3-way match logic (does the invoice match the PO and goods receipt?) and the shared Pydantic data schemas the whole team depends on.

**Key files:**
- `src/agent_on_duty/extraction/extract.py` — PDF text extraction
- `src/agent_on_duty/extraction/check.py` — 3-way match logic
- `src/agent_on_duty/contracts.py` — contract library loader
- `src/agent_on_duty/pipeline.py` — end-to-end pipeline
- `src/agent_on_duty/schemas.py` — shared data schemas

---

## Area 3 — ReAct Agent Loop & HITL Gate
**Report section:** §2 Research Questions, §4 Human-in-the-Loop

The brain of the system. A ReAct loop running on Qwen3-1.7B (1.7 billion parameters, running fully locally via Ollama) that calls tools, retrieves documents, checks discrepancies, and produces a recommendation. The HITL (Human-in-the-Loop) gate enforces that the agent can never write a final decision — only a human manager can do that. Also owns the SQLite audit log that records every step.

**Key files:**
- `src/agent_on_duty/agent/react.py` — the full agent loop (most complex file, 684 lines)
- `src/agent_on_duty/audit/store.py` — SQLite store + HITL enforcement

---

## Area 4 — OKF Retrieval & Frontend
**Report section:** §1 Introduction, §8 Conclusion

Owns Path B — the OKF (Open Knowledge Format) retrieval approach. Instead of searching a vector index, the agent navigates structured Markdown concept files (one per document, one per MSA section) with YAML metadata. Also owns the entire Next.js frontend: dashboard, verification view, approvals page, benchmark results.

**Key files:**
- `src/agent_on_duty/retrieval/path_b.py` — OKF bundle navigation
- `scripts/okf_bundle_converter.py` — converts PDFs into OKF concept files
- `web/` — full Next.js frontend (2,100+ lines across all pages)
- `docs/`, `README.md` — project documentation

---

## Area 5 — Vector RAG & Calculation Tools
**Report section:** §3 Theoretical Background

Owns Path A — the standard vector RAG retrieval approach. Splits PDFs into 500-token chunks, embeds them with nomic-embed-text (via Ollama), stores them in a FAISS index, and retrieves the top-5 most similar chunks for each query. Also owns the deterministic calculation tools (price variance, quantity variance, line-total checks) that the agent calls instead of doing arithmetic itself.

**Key files:**
- `src/agent_on_duty/retrieval/path_a.py` — FAISS vector search
- `src/agent_on_duty/retrieval/corpus.py` — corpus builder and FAISS index
- `src/agent_on_duty/tools/calc.py` — price, quantity, line-total calculation tools
- `src/agent_on_duty/cli.py` — command-line interface

---

## Area 6 — Dataset & Benchmark Generation
**Report section:** §7 Dataset Description, §9 Project Schedule

Built the synthetic benchmark from scratch. Two seed supplier relationships (packaging/fasteners and electronic components), each producing 12 package variants with injected discrepancies. Every package has known ground-truth flags so results can be scored. Also responsible for the project schedule and Gantt chart.

**Key files:**
- `scripts/seeds/` — seed relationships and variant generator (3,100+ lines)
- `scripts/dataset_generator.py` — entry point
- `data_pipeline/` — pipeline utilities
- `src/agent_on_duty/paths.py` — data directory path constants

---

After showing the areas, offer to: explain any area in more detail, show the actual code for any file, or walk through how the areas connect to each other.
