"""One live agent run through the real pipeline: uv run python scripts/smoke_agent.py PKG-023 A"""

import json
import sys
from pathlib import Path

from agent_on_duty import pipeline

pkg, path = sys.argv[1], sys.argv[2]


def show(s):
    calls = "; ".join(f"{c['name']}({json.dumps(c['arguments'])[:140]}) -> {c['result'][:100]!r}" for c in s.tool_calls) \
        if hasattr(s, "tool_calls") else ""
    print(f"step {s.step} ({s.seconds:.0f}s, {s.prompt_tokens} in, {s.output_tokens} out): {calls or 'TEXT ' + s.content[:120]!r}",
          flush=True)


run, _ = pipeline.verify(Path("data/packages") / pkg, path, Path("data/index"), on_step=show)
print("status:", run.status, "| invalid:", run.invalid_tool_calls, "| seconds:", run.seconds, flush=True)
print("recommendation:", run.recommendation.label if run.recommendation else None)
print("expected:      ", json.loads((Path("data/packages") / pkg / "ground_truth.json").read_text())["expected_recommendation"])
