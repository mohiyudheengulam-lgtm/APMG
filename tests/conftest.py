import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "seeds"))


@pytest.fixture(scope="session")
def bench(tmp_path_factory):
    """24 generated packages plus their contract library, in a temp folder."""
    from variants import generate

    root = tmp_path_factory.mktemp("bench")
    generate(root / "packages", seed=42, library=root / "contracts")
    return {"packages": sorted(p for p in (root / "packages").iterdir() if p.is_dir()), "library": root / "contracts"}


@pytest.fixture(scope="session")
def packages(bench):
    return bench["packages"]


@pytest.fixture(scope="session")
def library(bench):
    return bench["library"]
