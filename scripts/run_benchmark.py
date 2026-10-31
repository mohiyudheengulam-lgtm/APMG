"""Controlled benchmark (Exposé §6.2): every package × both paths × N sequential runs, after one discarded warm-up.

    uv run python scripts/run_benchmark.py --tag pilot --packages PKG-001 PKG-014 PKG-024 --runs 1
    uv run python scripts/run_benchmark.py --tag full            # 24 packages × 2 paths × 3 runs

Writes results/<tag>/{aod.sqlite, audit/*.json, manifest.json}. Re-running a tag skips finished
(package, path, run) combinations, so an interrupted benchmark can resume.
"""

import argparse
import json
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import ollama

from agent_on_duty import pipeline
from agent_on_duty.agent.react import MAX_STEPS, MODEL, RUN_OPTIONS, THINK
from agent_on_duty.audit.store import RecommendationWriter
from agent_on_duty.retrieval.path_a import EMBED_MODEL


def _sh(*cmd: str) -> str:
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=10).stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        return ""


def ollama_num_parallel() -> str | None:
    """Value the local Ollama app was started with (macOS launchctl env), if set."""
    return _sh("launchctl", "getenv", "OLLAMA_NUM_PARALLEL") or None


def manifest(args) -> dict:
    import faiss, pydantic, pymupdf  # noqa: E401 — versions only
    return {
        "started": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "hardware": {"cpu": _sh("sysctl", "-n", "machdep.cpu.brand_string") or platform.processor(),
                     "ram_bytes": _sh("sysctl", "-n", "hw.memsize"), "machine": platform.machine(),
                     "os": platform.platform()},
        "software": {"python": sys.version.split()[0], "ollama": _sh("ollama", "--version"),
                     "pymupdf": pymupdf.VersionBind, "faiss": faiss.__version__, "pydantic": pydantic.__version__},
        "ollama_num_parallel": ollama_num_parallel(),
        "model": MODEL, "embed_model": EMBED_MODEL, "run_options": RUN_OPTIONS, "think": THINK, "max_steps": MAX_STEPS,
        "packages": args.packages, "paths": args.paths, "runs": args.runs,
    }


def done_runs(audit_dir: Path) -> set[tuple[str, str, int]]:
    out = set()
    for f in audit_dir.glob("*.json"):
        r = json.loads(f.read_text())
        out.add((r["package_id"], r["retrieval_path"], r.get("run")))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="full")
    ap.add_argument("--packages", nargs="*", help="package ids (default: all)")
    ap.add_argument("--paths", nargs="+", default=["A", "B"])
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--data", type=Path, default=Path("data/packages"))
    ap.add_argument("--index", type=Path, default=Path("data/index"))
    ap.add_argument("--allow-parallel", action="store_true",
                    help="run even if OLLAMA_NUM_PARALLEL is not 1 (recorded in the manifest)")
    args = ap.parse_args()

    if ollama_num_parallel() != "1" and not args.allow_parallel:
        sys.exit("OLLAMA_NUM_PARALLEL is not 1 (Exposé §6.2). Run `launchctl setenv OLLAMA_NUM_PARALLEL 1`, "
                 "restart the Ollama app, then retry — or pass --allow-parallel for a non-final run.")

    pkgs = sorted(p for p in args.data.iterdir() if p.is_dir() and (not args.packages or p.name in args.packages))
    args.packages = [p.name for p in pkgs]
    out = Path("results") / args.tag
    out.mkdir(parents=True, exist_ok=True)
    (out / "manifest.json").write_text(json.dumps(manifest(args), indent=1))
    writer = RecommendationWriter(out / "aod.sqlite", out / "audit")

    for pdir in pkgs:  # preparation (criterion 4) — timed, not part of verification latency
        for path in args.paths:
            pipeline.prepare(pdir, path, args.index)

    print("warm-up (discarded) ...", flush=True)
    for path in args.paths:
        pipeline.verify(pkgs[0], path, args.index)

    done = done_runs(out / "audit")
    todo = [(p, path, r) for r in range(1, args.runs + 1) for p in pkgs for path in args.paths
            if (p.name, path, r) not in done]
    print(f"{len(todo)} verifications to run (sequential)", flush=True)
    t0 = time.perf_counter()
    for i, (pdir, path, r) in enumerate(todo, 1):
        run, vid = pipeline.verify(pdir, path, args.index, writer, extra={"run": r, "tag": args.tag})
        rec = run.recommendation.label if run.recommendation else "-"
        eta = (time.perf_counter() - t0) / i * (len(todo) - i) / 60
        print(f"[{i}/{len(todo)}] {pdir.name} {path} run{r}: {run.status.value} {run.seconds:.0f}s {rec}  (eta {eta:.0f} min)",
              flush=True)


if __name__ == "__main__":
    main()
