"""End-to-end pipeline per retrieval path: raw PDFs → (own extraction + index/bundle) → agent → PENDING_REVIEW."""

import json
from pathlib import Path

from agent_on_duty.agent.react import AgentRun, PathATools, PathBTools, Verifier
from agent_on_duty.audit.store import RecommendationWriter
from agent_on_duty.retrieval import path_b
from agent_on_duty.retrieval.path_a import PathAIndex
from agent_on_duty.retrieval.path_b import PathBBundle


def prepare(package_dir: Path, path: str, index_root: Path, rebuild: bool = False) -> dict:
    """Build Path A index or Path B bundle (each runs its own extraction). Cached unless rebuild."""
    out = index_root / path / package_dir.name
    if (out / "build.json").exists() and not rebuild:
        return json.loads((out / "build.json").read_text())
    return PathAIndex.build(package_dir, out) if path == "A" else path_b.convert(package_dir, out)


def retrieval_for(package_dir: Path, path: str, index_root: Path) -> PathATools | PathBTools:
    out = index_root / path / package_dir.name
    return PathATools(PathAIndex.load(out)) if path == "A" else PathBTools(PathBBundle(out))


def verify(package_dir: Path, path: str, index_root: Path, writer: RecommendationWriter | None = None,
           extra: dict | None = None, on_step=None) -> tuple[AgentRun, str | None]:
    build = prepare(package_dir, path, index_root)
    run = Verifier(package_dir.name, retrieval_for(package_dir, path, index_root),
                   documents=build.get("documents")).verify(on_step=on_step)
    vid = writer.save(run, (extra or {}) | {"build": build}) if writer else None
    return run, vid
