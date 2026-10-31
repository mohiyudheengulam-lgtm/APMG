"""Generate the benchmark: data/packages/PKG-NNN/{*.pdf, ground_truth.json}."""

import argparse
from collections import Counter
from pathlib import Path

from agent_on_duty.benchmark.generator import generate

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/packages"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    gts = generate(args.out, args.seed)
    print(f"{len(gts)} packages → {args.out}")
    for rec, n in sorted(Counter(g["expected_recommendation"] for g in gts).items()):
        print(f"  {n:2d}  {rec}")
