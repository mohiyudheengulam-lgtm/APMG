import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "seeds"))


@pytest.fixture(scope="session")
def packages(tmp_path_factory):
    from variants import generate

    out = tmp_path_factory.mktemp("packages")
    generate(out, seed=42)
    return sorted(p for p in out.iterdir() if p.is_dir())
