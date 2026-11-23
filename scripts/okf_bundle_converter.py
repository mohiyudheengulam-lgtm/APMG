"""Convert benchmark packages into OKF v0.2 bundles: <index-root>/B/<PKG>/.

Uses the same code path as the app and the benchmark (pipeline.prepare), so each bundle also links the MSA and
purchasing guideline from the contract library. Library contracts are built once under <index-root>/B/contracts/.
"""

import argparse
from pathlib import Path

from agent_on_duty import contracts, pipeline

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", type=Path, default=Path("data/packages"))
    ap.add_argument("--index-root", type=Path, default=Path("data/index"), help="bundles go to <index-root>/B/<PKG>")
    ap.add_argument("--library", type=Path, default=contracts.LIBRARY, help="contract library folder")
    ap.add_argument("--rebuild", action="store_true",
                    help="rebuild package bundles (library contracts stay cached: delete <index-root>/B/contracts to rebuild those)")
    args = ap.parse_args()
    if not any(args.library.glob("*/contract.json")):
        print(f"! No contracts in {args.library}: bundles will have no MSA or guideline. "
              "Run scripts/dataset_generator.py or add contracts in the app first.")
    for pdir in sorted(p for p in args.packages.iterdir() if p.is_dir()):
        stats = pipeline.prepare(pdir, "B", args.index_root, rebuild=args.rebuild, lib=args.library)
        print(f"{pdir.name}: {stats['concepts']} concepts, contracts={stats['contracts']}, {stats['build_seconds']}s")
