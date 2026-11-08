# Benchmark results and design deviation: assisted mode

Status: draft for team review · run `full-assisted`, 2026-11-08 · Apple M2, 8 GB · Qwen3-1.7B, temperature 0,
seed 42, max 10 steps, 500/50 chunks, top-5, `OLLAMA_NUM_PARALLEL=1` (all settings as in Exposé §6.2).

## 1. Deviation from the Exposé

Exposé §6.2 has the agent extract the invoice, purchase order and goods receipt itself through each retrieval
path, and TEAM_MANUAL §5 says results only count from research mode. The final benchmark instead runs in
**assisted mode**:

- Invoice, PO and goods receipt are extracted by the deterministic pipeline (`pipeline.check_package`) and
  pre-submitted to the agent, together with the result of the price/quantity/line-total checks and the list of
  missing documents. On the generated corpus this extraction matches the ground truth for all 24 packages.
- The agent's task is reduced to the contract work: if the invoice has surcharges, retrieve the MSA surcharge
  clause through its path, call `check_surcharge` with the clause's document and page, then `finish`.
- Both paths get the same assisted prompt (only the retrieval sentence differs, as in research mode) and the same
  tools (`check_surcharge`, `finish` plus the path's retrieval tool). Model and run settings are unchanged.

**Why.** In research mode the 1.7B model could not complete the extraction step through Path A (pilot on 9 case
types, 1 run each: Path A 0/9 — every run hit the 10-step limit; Path B 8/9). The exposé's top-5 vector search
almost always returns MSA and guideline chunks instead of invoice/PO line items, and the model then loops. Even
when the right rows were shown, the model sometimes copied the invoice value instead of the differing goods-receipt
value. A comparison in which one path never finishes measures the step limit, not retrieval quality.

**Consequences for the evaluation.**

- Field EM and calculation EM are 100 % for both paths by construction (they come from extraction). They no longer
  compare the paths and are reported only as a property of the pipeline.
- The retrieval comparison rests on **clause citation** in the 6 surcharge packages (PKG-004, 010, 011, 016, 021,
  023). Runs at temperature 0 are identical across repetitions, so this is effectively n = 6 per path.
- Packages without surcharges need no retrieval; both paths just call `finish` (≈ 1 s, 1 step).
- The research-mode result above is reported as a finding in its own right (SQ1), not discarded.

## 2. Results (`full-assisted`, 24 packages × 2 paths × 3 runs = 144 runs)

| Metric | Path A (vector RAG) | Path B (OKF) |
|---|---|---|
| Correct recommendation | 100 % | 100 % |
| Flag micro F1 (all five flags) | 1.00 | 1.00 |
| Field / calculation EM | 100 % / 100 % (from extraction) | 100 % / 100 % (from extraction) |
| **Clause citation correct** | **50 %** (3/6 packages) | **33 %** (2/6 packages) |
| Median seconds / verification | 1.5 | 1.4 |
| Mean input tokens / verification | 3 526 | 2 796 |
| Invalid tool-call rate | 0 % | 8.5 % |
| Step limit reached | 0 % | 0 % |
| Evidence complete | 87.5 % | 83.3 % |
| Build time, all packages (incl. extraction) | 14.6 s | 3.0 s |
| Storage, all packages | 705 KB | 76 KB |
| Contract library: build / storage | 5.6 s / 281 KB | 0.2 s / 117 KB |
| Decisions without manager sign-off | 0 | 0 |

Citations per surcharge package (identical in all 3 runs):

| Package | Contract | Correct page | Path A cited | Path B cited |
|---|---|---|---|---|
| PKG-004 | MSA-LFT-PKV-2026-01 | 9 | 9 ✓ | 27 ✗ (clause number used as page, cited `msa/index.md`) |
| PKG-010 | MSA-LFT-PKV-2026-01 | 9 | 5 ✗ | 9 ✓ |
| PKG-011 | MSA-LFT-PKV-2026-01 | 9 | 27 ✗ (clause number used as page) | 9 ✓ |
| PKG-016 | RV-QE-SC-2026-003 | 11 | 11 ✓ | 5 ✗ (opened § 8 Prices, not § 28 Surcharges) |
| PKG-021 | RV-QE-SC-2026-003 | 11 | 11 ✓ | 5 ✗ (same) |
| PKG-023 | RV-QE-SC-2026-003 | 11 | 8 ✗ | 5 ✗ (same) |

All six surcharges were correctly judged not allowed by both paths, so the flags are right even where the citation
is wrong.

## 3. Interpretation (descriptive, §6.5)

1. **Research mode:** with a 1.7B model, the agent cannot extract structured documents through vector RAG at the
   exposé settings; through OKF navigation it mostly can. This is the clearest path difference observed.
2. **Assisted mode:** with extraction done by code, the system is reliable (100 % correct recommendations, no step
   limits, no decisions without sign-off). The model's remaining weakness is citing the right clause page:
   about 40–50 % on both paths. The 3-vs-2 difference is too small to prefer either path for MSA clauses.
3. **Cost:** Path B uses ~20 % fewer input tokens and far less build time and storage; Path A had fewer invalid
   tool calls (Path B's model guessed non-existent paths such as `msa/MSA-LFT-PKV-2026-01.pdf`).
4. **SQ3 routing:** `evaluate.py` assigns MSA clauses to Path A because citation differs by 16.7 pp. That
   rule was written for larger samples; with n = 6 it is one package, so we report it as inconclusive.

## 4. Invalid runs

`bench1` and all pilots before `pilot19-assisted` used earlier agent versions (German-decimal parsing bug,
same-turn read-and-submit fabrication on Path B, research-mode prompt in assisted runs). They are not results.

## 5. Reproduce

```bash
uv run python scripts/run_benchmark.py --tag full-assisted --assisted   # ~20 min on an M2
uv run python scripts/evaluate.py --tag full-assisted --assisted       # results/full-assisted/summary.md
```

## 6. For team decision

- Accept assisted mode as the reported design (and update TEAM_MANUAL §5 "results only count from research mode").
- Whether `check_surcharge` should reject a cited page the agent never retrieved (same rule for both paths). It
  would stop citations like "index file, page 27", but adds another guard; it requires a re-run (~20 min).
