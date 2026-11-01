"""Generate the benchmark: data/packages/PKG-NNN/{*.pdf, ground_truth.json}.

24 packages expanded from the two realistic seed packages (scripts/seeds/variants.py).
"""

import argparse
import sys
from collections import Counter
from pathlib import Path

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=Path("data/packages"))
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    sys.path.insert(0, str(Path(__file__).resolve().parent / "seeds"))
    from variants import generate
    gts = generate(args.out, args.seed)
    print(f"{len(gts)} packages → {args.out}")
    for rec, n in sorted(Counter(g["expected_recommendation"] for g in gts).items()):
        print(f"  {n:2d}  {rec}")
