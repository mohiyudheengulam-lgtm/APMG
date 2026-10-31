# APMG — Agent On Duty

Uni group project (APMG module). Full exposé: `docs/expose.md`.

**One-liner:** fully local ReAct agent (Qwen3-1.7B via Ollama) doing three-way match
(PO / goods receipt / invoice) + MSA surcharge checks, with a mandatory human approval gate.
Research core = controlled comparison of **Path A (vector RAG: 500/50 chunks, nomic-embed-text, FAISS top-5)**
vs **Path B (OKF v0.2 concept navigation)**.

## Team / sections
1 Intro, 8 Justification – Navya Gupta · 2 RQs, 4 HITL – Rishikta Nishikant Bhore ·
3 Theory – Vijayadharshan Periyasamy · 5 Architecture – Sara Shaban ·
**6 Methodology & evaluation – Mohiyudheen Kalluparamban** · 7 Data, 9 Schedule – Allen Smith

## Fixed design decisions (don't drift — they're the experimental controls)
- Same extraction *configuration*, model, prompt, tools, schema, settings for both paths; each path
  extracts independently from raw files (extraction time counts as that path's build time)
- temperature 0, fixed seed, max 10 steps; 3 sequential runs/package/path + 1 discarded warm-up,
  Ollama started with `OLLAMA_NUM_PARALLEL=1`
- Flags: PRICE, QUANTITY, LINE_TOTAL, SURCHARGE, MISSING_DOCUMENT (`FLAGGED_*`); tax rate extracted + validated, not rule-checked
- Arithmetic only in `tools/calc.py`, never by the model
- Agent output = `Recommendation` (flags). Final `Decision` only via the approval function → SQLite
- Out of scope: tax rules, multi-currency, OCR evaluation, dynamic router (SQ3 is post-hoc)

## Schedule
- Exposé due **Tue 2026-11-03**
- S1 Nov 4–17: Ollama, seed templates, `scripts/dataset_generator.py` + ground truth, PyMuPDF extraction
- S2 Nov 18–Dec 1: Path A + `okf_bundle_converter.py` (Path B)
- S3 Dec 2–15: ReAct loop, Pydantic tools, SQLite + JSON audit, HITL gate (mid-review demo)
- S4A Dec 16–22: Streamlit UI + pilot run on 2–3 packages · holiday Dec 23–Jan 7
- S4B/5 Jan 8–15: integration + benchmark · S6 Jan 16–22: report, poster, live demo (**Fri 2027-01-22**)

## Status
- 2026-10-31: exposé revision (sections 1–10) applied: LINE_TOTAL flag, tax-rate field, independent per-path extraction
- 2026-10-31: benchmark generator (24 pkgs, PDFs + ground truth) + PyMuPDF extraction, 100% field match
- 2026-10-31: repo scaffolded; schemas + deterministic calc tools + tests (exposé €590 example passes)
