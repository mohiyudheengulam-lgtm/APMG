"""Where Agent On Duty keeps its data.

From a source checkout: the repository (data/, results/). Installed as a tool: ~/AgentOnDuty.
Override with the AOD_HOME environment variable.
"""

import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]


def home() -> Path:
    if os.environ.get("AOD_HOME"):
        return Path(os.environ["AOD_HOME"]).expanduser()
    if (_REPO / "pyproject.toml").exists() and (_REPO / "src" / "agent_on_duty").exists():
        return _REPO
    return Path.home() / "AgentOnDuty"


HOME = home()
DATA = HOME / "data"
PACKAGES = DATA / "packages"
UPLOADS = DATA / "uploads"
INDEX = DATA / "index"
CONTRACTS = DATA / "contracts"
RESULTS = HOME / "results"
WEB_BUILD = Path(__file__).resolve().parent / "webui"  # static web app (built by scripts/build_app.sh)
