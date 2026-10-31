"""Build all synthetic seed procurement packages.

Usage:  (from the repo root)  uv run python scripts/seeds/build_seeds.py [1|2 ...]
Outputs to data/seeds/<package_name>/ ; PNG previews go to the session scratchpad (common.PREVIEW_DIR).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import package_1  # noqa: E402
import package_2  # noqa: E402
from pipeline import build  # noqa: E402

PACKAGES = {"1": package_1, "2": package_2}


def main(argv: list[str]) -> None:
    for key in argv or list(PACKAGES):
        result = build(PACKAGES[key])
        print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:])
