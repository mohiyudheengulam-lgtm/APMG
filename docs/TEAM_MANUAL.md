# Agent On Duty — Team Manual

Prototype for the APMG project: a fully local AI agent that checks supplier invoices against the purchase order,
delivery note, goods receipt and the supplier's master agreement (MSA), and prepares an evidence-backed
recommendation. **A manager always makes the final decision.** The research compares two retrieval methods:
**Path A – vector RAG** and **Path B – OKF concept navigation** (see `docs/expose.md`).

Contents: [1 Install](#1-install-just-use-the-app) · [2 Using the app](#2-using-the-app) ·
[3 Who owns what](#3-who-owns-what-section-division) · [4 Developer setup](#4-developer-setup) ·
[5 Working together in git](#5-working-together-in-git) · [6 Benchmark rules](#6-running-the-benchmark-research-rules) ·
[7 Troubleshooting](#7-troubleshooting)

---

## 1. Install (just use the app)

You need: **Ollama** (local AI runtime) and **uv** (Python tool manager). Works on macOS, Windows and Linux.
An Apple Silicon Mac (M1–M4) or a PC with an NVIDIA GPU is strongly recommended — on an older Intel laptop one
check takes 10–20 minutes instead of about one.

1. Download the installer `agent_on_duty-<version>-py3-none-any.whl` from the repository's **Releases** page.
2. Install the tools and the two models:

   macOS / Linux
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   # install Ollama from https://ollama.com and start it
   ollama pull qwen3:1.7b
   ollama pull nomic-embed-text
   uv tool install ~/Downloads/agent_on_duty-0.1.0-py3-none-any.whl
   ```
   Windows (PowerShell)
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   # install Ollama from https://ollama.com and start it
   ollama pull qwen3:1.7b
   ollama pull nomic-embed-text
   uv tool install $HOME\Downloads\agent_on_duty-0.1.0-py3-none-any.whl
   ```
3. Start it:
   ```bash
   agent-on-duty --demo     # first time: loads 24 demo packages + 2 supplier contracts, opens the browser
   agent-on-duty            # afterwards
   ```
   The app runs at http://localhost:8000. Your data lives in `~/AgentOnDuty` (change with `AOD_HOME`).

**Showing it to others on the same network:** `agent-on-duty --host 0.0.0.0`, then open `http://<your-IP>:8000`.
⚠ The app has no login yet — only do this on a trusted network (home/team), never on public Wi-Fi.

---

## 2. Using the app

| Page | What you do there |
|---|---|
| **Contracts** | Add each supplier's master agreement (MSA) and the buyer's purchasing guideline **once**. The contract number and parties are read automatically; invoices/POs quoting that number are linked to it. You can edit the match terms or remove a contract. |
| **Verify** | Pick a package (PO, delivery note, goods receipt, invoice) or upload one. Check the two boxes at the top of the run panel: **"From the contract library"** (is the MSA linked?) and **"Extraction verified"** (✓ = the extracted lines reproduce the documents' own totals). Choose **Path A** or **Path B** and press **Run verification**. **Batch run** queues many packages (e.g. overnight). |
| **Evidence** | Every verification: findings with amounts and formulas, the cited PDF page next to it, every agent step with time and tokens, the values the agent submitted. |
| **Approvals** | The human-in-the-loop gate: **Confirm**, **Override** (written reason required) or **Reject**. Only this records a final decision. |
| **Overview** | KPIs and charts across all verifications. |
| **Benchmark** | Path A vs Path B results of a benchmark run (all evaluation criteria of Exposé §6.3). |

**Research mode vs assisted mode** (checkbox on Verify):

| | Research mode (default) | Assisted mode |
|---|---|---|
| Who reads invoice, PO, goods receipt | the AI agent, via Path A or B | the extraction code (pre-filled) |
| What the agent does | everything | only the contract check (surcharges) |
| Speed | slow (5–8 model steps) | fast (2–3 steps) |
| Used in the benchmark | **yes — the only mode used** | no, excluded automatically |
| Available | always | only if the extraction is ✓ verified, otherwise it falls back to research mode |

---

## 3. Who owns what (section division)

One owner per part, matching the exposé sections each person wrote. *Proposed — adjust in the team meeting and
update this table and `.github/CODEOWNERS`.*

| Owner | Exposé | Part | Code | What you tune / improve |
|---|---|---|---|---|
| **Allen Smith** | §7, §9 | Benchmark data | `scripts/seeds/`, `data/seeds/` | more suppliers/layouts, new case types (e.g. *allowed* surcharges), ground truth |
| **Sara Shaban** | §5 | Extraction + contract library | `src/agent_on_duty/extraction/`, `contracts.py` | new invoice layouts, self-check, OCR fallback |
| **Vijayadharshan Periyasamy** | §3 | Path A — vector RAG | `src/agent_on_duty/retrieval/path_a.py`, `corpus.py` | chunking, embeddings, FAISS search |
| **Navya Gupta** | §1, §8 | Path B — OKF | `src/agent_on_duty/retrieval/path_b.py` | concept files, MSA section splitting, links, index |
| **Rishikta Nishikant Bhore** | §2, §4 | Agent + approval gate | `src/agent_on_duty/agent/`, `audit/`, `tools/` | prompt, tools, guards, compaction, HITL, audit record |
| **Mohiyudheen Kalluparamban** | §6 | Evaluation + integration | `pipeline.py`, `api.py`, `cli.py`, `web/`, `scripts/run_benchmark.py`, `scripts/evaluate.py` | metrics, benchmark runs, app, releases, merges into `main` |

**Shared, changes need two owners' approval:** `src/agent_on_duty/schemas.py` (the data types every part
exchanges), `pyproject.toml`, the agent's run settings (model, temperature, seed, step limit), `docs/expose.md`.

---

## 4. Developer setup

```bash
git clone git@github.com:mohiyudheengulam-lgtm/APMG.git apmg && cd apmg
uv sync                                        # Python packages
uv run python scripts/dataset_generator.py     # 24 packages + contract library (from the committed seeds)
uv run pytest                                  # 26 tests, ~1 min, no AI model needed
cd web && npm install && cd ..                 # web app (needs Node.js 20+)
scripts/dev.sh                                 # API :8000 + app http://localhost:3100 with hot reload
```
Ollama settings for benchmark machines: see `SETUP.md`. Speed check: `uv run python scripts/speed_check.py`.

Repository map:
```
src/agent_on_duty/   extraction/ retrieval/ agent/ audit/ tools/ contracts.py pipeline.py api.py cli.py schemas.py
scripts/             seeds/ (benchmark data) dataset_generator.py run_benchmark.py evaluate.py build_app.sh dev.sh
web/                 Next.js app          tests/  automated tests (scripted model, no LLM)
docs/                expose.md  system-overview.html  TEAM_MANUAL.md
```
Start with `CONTEXT.md` (design decisions) and `docs/system-overview.html` (visual walkthrough).

---

## 5. Working together in git

1. Never commit directly to `main`. Create a branch: `git checkout -b pathA/chunk-overlap`.
2. Change only your part. If you need something from another part, ask its owner (or open an issue).
3. Run `uv run pytest` (and `cd web && npx tsc --noEmit` for app changes) before pushing.
4. Push and open a **pull request**; the owner of the touched folder reviews it. Explain *what* and *why*,
   and for research-relevant changes say how the result changes.
5. Mohiyudheen merges into `main` and tags releases (`git tag v0.1.1 && git push origin v0.1.1` builds the installer).

Rules that protect the research:
- **Never change the experiment settings on your own** (Qwen3-1.7B, temperature 0, seed 42, max 10 steps,
  500-token chunks / 50 overlap / top-5, `OLLAMA_NUM_PARALLEL=1`). They are the controls of the comparison.
- Both paths must get **the same** extraction, prompt, tools and run settings — improvements to one path must not
  leak into the shared agent unless agreed.
- Results only count from **research mode**, on the benchmark machine, with the run's `manifest.json` kept.
- Generated data (`data/packages`, `data/index`, `data/contracts`, `results/`) is never committed.

---

## 6. Running the benchmark (research rules)

Only on the agreed benchmark machine (Apple Silicon / GPU), all runs on the same machine:
```bash
# Ollama settings (see SETUP.md), then:
uv run python scripts/run_benchmark.py --tag pilot --packages PKG-001 PKG-011 PKG-023 --runs 1
uv run python scripts/run_benchmark.py --tag full      # 24 packages × 2 paths × 3 runs, resumable
uv run python scripts/evaluate.py --tag full           # results/full/summary.md → Benchmark page
```
The runner refuses to start unless `OLLAMA_NUM_PARALLEL=1`, discards one warm-up run, runs sequentially and
records hardware, software versions and settings in `results/<tag>/manifest.json`.

---

## 7. Troubleshooting

| Symptom | Cause / fix |
|---|---|
| A check takes 10–20 min, laptop gets hot | The model is slow on CPU-only machines. Use an Apple Silicon/GPU machine, assisted mode, or batch runs overnight. |
| "Cannot reach the local API" | API not running (`agent-on-duty` or `scripts/dev.sh`). A single hiccup under load is ignored automatically. |
| "Ollama is not running" / model missing | Start Ollama; `ollama pull qwen3:1.7b` and `ollama pull nomic-embed-text`. |
| Package shows ⚠ *Extraction uncertain* | The extracted lines don't match the document's printed totals — check the values by hand; tell Sara (extraction owner) and attach the PDF. |
| "no contract linked" on Verify | Add the supplier's MSA under Contracts, or edit its match terms to the number printed on the invoice/PO. |
| Ollama settings gone after reboot (macOS) | `launchctl setenv` does not survive restarts — repeat the commands in `SETUP.md`. |
