"""How fast is this machine for the benchmark? Takes 1–3 minutes on a slow CPU, seconds on Apple Silicon / GPU.

    uv run python scripts/speed_check.py
"""

import time

import ollama

from agent_on_duty.agent.react import MODEL, RUN_OPTIONS, THINK

PROMPT_TOKENS_PER_STEP = 4000   # typical agent context per step after compaction
STEPS_PER_RUN = 7
RUNS = 24 * 2 * 3 + 2           # 24 packages × 2 paths × 3 runs + warm-up

filler = "The supplier shall deliver the goods in accordance with the agreed price list and delivery terms. " * 120
t = time.perf_counter()
r = ollama.chat(model=MODEL, messages=[{"role": "user", "content": filler + "\nCount to twenty, separated by commas."}],
                options=RUN_OPTIONS, think=THINK)
prompt_rate = r.prompt_eval_count / (r.prompt_eval_duration / 1e9)
gen_rate = r.eval_count / max(r.eval_duration / 1e9, 1e-9)
step = PROMPT_TOKENS_PER_STEP / prompt_rate + 120 / gen_rate  # worst case: full prompt re-read, ~120 output tokens
print(f"prompt reading : {prompt_rate:7.0f} tokens/s  ({r.prompt_eval_count} tokens)")
print(f"generation     : {gen_rate:7.1f} tokens/s")
print(f"per agent step : ~{step:5.0f} s (upper estimate)")
print(f"per verification: ~{step * STEPS_PER_RUN / 60:4.1f} min")
print(f"full benchmark ({RUNS} runs): ~{step * STEPS_PER_RUN * RUNS / 3600:4.1f} h")
print(f"(measured in {time.perf_counter() - t:.0f} s)")
