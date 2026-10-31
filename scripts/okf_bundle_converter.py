"""Convert benchmark packages into OKF v0.2 bundles: data/index/B/<PKG>/."""

import argparse
from pathlib import Path

from agent_on_duty.retrieval.path_b import convert

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--packages", type=Path, default=Path("data/packages"))
    ap.add_argument("--out", type=Path, default=Path("data/index/B"))
    args = ap.parse_args()
    for pdir in sorted(p for p in args.packages.iterdir() if p.is_dir()):
        print(convert(pdir, args.out / pdir.name))
