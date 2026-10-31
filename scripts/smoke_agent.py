"""One live agent run: uv run python scripts/smoke_agent.py PKG-024 A"""

import json
import sys
from pathlib import Path

from agent_on_duty.agent.react import PathATools, PathBTools, Verifier
from agent_on_duty.retrieval.path_a import PathAIndex
from agent_on_duty.retrieval.path_b import PathBBundle

pkg, path = sys.argv[1], sys.argv[2]
retrieval = (PathATools(PathAIndex.load(Path(f"data/index/A/{pkg}"))) if path == "A"
             else PathBTools(PathBBundle(Path(f"data/index/B/{pkg}"))))
run = Verifier(pkg, retrieval).verify()
for s in run.steps:
    print(f"step {s.step} ({s.seconds}s, {s.prompt_tokens} in): "
          + "; ".join(f"{c['name']}({json.dumps(c['arguments'])[:150]}) -> {c['result'][:120]!r}" for c in s.tool_calls)
          + (f" TEXT: {s.content[:150]!r}" if not s.tool_calls else ""))
print("status:", run.status, "| invalid:", run.invalid_tool_calls, "| seconds:", run.seconds)
print("recommendation:", run.recommendation.label if run.recommendation else None)
gt = json.loads(Path(f"data/packages/{pkg}/ground_truth.json").read_text())
print("expected:      ", gt["expected_recommendation"])
