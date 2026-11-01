# Setup — running Agent On Duty on another machine

Use one machine for the whole benchmark (Exposé §6.2). Apple Silicon (M1–M4) or a PC with an NVIDIA GPU is
10–50× faster than an Intel Mac; `scripts/speed_check.py` tells you within minutes.

## 1. Install (macOS)
```bash
brew install uv node git
brew install --cask ollama          # or download the Ollama app
ollama pull qwen3:1.7b
ollama pull nomic-embed-text
```

## 2. Ollama settings (required for the benchmark)
Sequential requests (§6.2), flash attention and an 8-bit KV cache. On macOS:
```bash
launchctl setenv OLLAMA_NUM_PARALLEL 1
launchctl setenv OLLAMA_FLASH_ATTENTION 1
launchctl setenv OLLAMA_KV_CACHE_TYPE q8_0
# then quit and reopen the Ollama app
```
`launchctl setenv` is lost on reboot — repeat after a restart. The benchmark refuses to start unless
`OLLAMA_NUM_PARALLEL` is 1, and every run's `manifest.json` records all three values.
On Linux set them in the `ollama.service` environment instead.

## 3. Project
```bash
git clone <repo-url> apmg && cd apmg
uv sync
uv run python scripts/seeds/build_seeds.py      # seed packages (deterministic)
uv run python scripts/dataset_generator.py      # 24 benchmark packages + contract library (2 MSAs, 2 guidelines)
uv run pytest                                   # 16 tests, ~1 min
uv run python scripts/speed_check.py            # how long will the benchmark take here?
cd web && npm install && cd ..
```
Build indexes on the benchmark machine itself (they are created automatically; never copy `data/index/`).

## 4. Run
```bash
scripts/dev.sh                                         # app: http://localhost:3100 (API on :8000)
uv run python scripts/run_benchmark.py --tag pilot --packages PKG-001 PKG-011 PKG-023 --runs 1
uv run python scripts/run_benchmark.py --tag full      # 24 × 2 paths × 3 runs, resumable
uv run python scripts/evaluate.py --tag full           # results/full/summary.md → Benchmark page
```
Assisted mode (pre-filled values, app only) is never used by the benchmark and is excluded from evaluation.
