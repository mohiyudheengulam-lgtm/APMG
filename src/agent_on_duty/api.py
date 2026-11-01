"""Local HTTP API for the Next.js UI (web/). Wraps the pipeline; adds no new decision paths.

    uv run uvicorn agent_on_duty.api:app --port 8000

Verifications run one at a time on a single worker thread (Ollama is used sequentially, as in the benchmark).
Final decisions are still written only by audit.store.approve().
"""

import csv
import json
import queue
import re
import shutil
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

from agent_on_duty import pipeline
from agent_on_duty.audit.store import RecommendationWriter, approve, list_verifications
from agent_on_duty.schemas import Decision

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
PACKAGES = DATA / "packages"
UPLOADS = DATA / "uploads"
INDEX = DATA / "index"
RESULTS = ROOT / "results"
APP_DIR = RESULTS / "app"
WRITER = RecommendationWriter(APP_DIR / "aod.sqlite", APP_DIR / "audit")
SAFE = re.compile(r"^[A-Za-z0-9._-]{1,80}$")

app = FastAPI(title="Agent On Duty API")


# ------------------------------------------------------------------ helpers

def _safe(name: str) -> str:
    if not SAFE.match(name) or name.startswith("."):
        raise HTTPException(400, f"invalid name: {name}")
    return name


def _source_dir(source: str) -> Path:
    d = APP_DIR if source == "app" else RESULTS / _safe(source)
    if source != "app" and not (d / "aod.sqlite").exists():
        raise HTTPException(404, f"unknown source {source}")
    return d


def _package_dir(pkg: str) -> Path:
    for base in (PACKAGES, UPLOADS):
        if (base / _safe(pkg)).is_dir():
            return base / pkg
    raise HTTPException(404, f"unknown package {pkg}")


def _audit(path: str) -> dict:
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return {}


def _rows(source: str) -> list[dict]:
    db = _source_dir(source) / "aod.sqlite"
    if not db.exists():
        return []
    out = []
    for r in list_verifications(db):
        a = _audit(r["audit_path"])
        findings = a.get("findings") or []
        out.append({
            "id": r["id"], "package_id": r["package_id"], "path": r["path"], "created_at": r["created_at"],
            "run_status": r["run_status"], "recommendation": r["recommendation"],
            "flags": [] if not r["recommendation"] or r["recommendation"] == "NO_DISCREPANCY" else r["recommendation"].split(","),
            "review_state": r["review_state"], "decision": r["decision"], "reviewer": r["reviewer"],
            "decided_at": r["decided_at"], "override_reason": r["override_reason"],
            "impact_eur": float(sum((Decimal(str(f.get("amount") or 0)) for f in findings), Decimal(0))),
            "seconds": a.get("seconds_total"), "prompt_tokens": a.get("prompt_tokens_total"),
            "steps": len(a.get("steps") or []), "invalid_tool_calls": a.get("invalid_tool_calls"), "run": a.get("run"),
        })
    return out


# ------------------------------------------------------------------ read endpoints

@app.get("/api/sources")
def sources():
    out = [{"id": "app", "label": "This workstation"}]
    if RESULTS.exists():
        out += [{"id": d.name, "label": f"Benchmark · {d.name}"} for d in sorted(RESULTS.iterdir())
                if d.name != "app" and (d / "aod.sqlite").exists()]
    return out


@app.get("/api/verifications")
def verifications(source: str = "app"):
    return _rows(source)


@app.get("/api/overview")
def overview(source: str = "app"):
    rows = _rows(source)
    flags: dict[str, int] = {}
    for r in rows:
        for f in r["flags"]:
            flags[f] = flags.get(f, 0) + 1
    secs = sorted(r["seconds"] for r in rows if r["seconds"] is not None)
    pending = [r for r in rows if r["review_state"] == "PENDING_REVIEW"]
    by_day: dict[str, int] = {}
    for r in rows:
        by_day[r["created_at"][:10]] = by_day.get(r["created_at"][:10], 0) + 1
    return {
        "total": len(rows),
        "packages": len({r["package_id"] for r in rows}),
        "pending": len(pending),
        "pending_flagged": sum(bool(r["flags"]) for r in pending),
        "flagged": sum(bool(r["flags"]) for r in rows),
        "no_result": sum(r["recommendation"] is None for r in rows),
        "clean": sum(r["recommendation"] == "NO_DISCREPANCY" for r in rows),
        "reviewed": sum(r["review_state"] == "REVIEWED" for r in rows),
        "overrides": sum(r["decision"] == "OVERRIDDEN" for r in rows),
        "impact_eur": sum(r["impact_eur"] for r in rows),
        "median_seconds": secs[len(secs) // 2] if secs else None,
        "flags": flags,
        "by_path": {p: sum(r["path"] == p for r in rows) for p in ("A", "B")},
        "by_day": by_day,
    }


@app.get("/api/verifications/{vid}")
def verification(vid: str, source: str = "app"):
    row = next((r for r in list_verifications(_source_dir(source) / "aod.sqlite") if r["id"] == _safe(vid)), None)
    if row is None:
        raise HTTPException(404)
    audit = _audit(row["audit_path"])
    gt_file = _package_dir(row["package_id"]) / "ground_truth.json" if row["package_id"] else None
    expected = json.loads(gt_file.read_text())["expected_recommendation"] if gt_file and gt_file.exists() else None
    return {"row": dict(row), "audit": audit, "expected": expected}


class DecisionIn(BaseModel):
    decision: Decision
    reviewer: str
    override_reason: str | None = None


@app.post("/api/verifications/{vid}/decision")
def decide(vid: str, body: DecisionIn, source: str = "app"):
    if not body.reviewer.strip():
        raise HTTPException(400, "reviewer is required")
    try:
        md = approve(_source_dir(source) / "aod.sqlite", _safe(vid), body.decision, body.reviewer.strip(),
                     (body.override_reason or "").strip() or None)
    except KeyError:
        raise HTTPException(404)
    except ValueError as e:
        raise HTTPException(400, str(e))
    return json.loads(md.model_dump_json())


# ------------------------------------------------------------------ packages

@app.get("/api/packages")
def packages():
    out = []
    for base, kind in ((PACKAGES, "benchmark"), (UPLOADS, "upload")):
        if not base.exists():
            continue
        for p in sorted(base.iterdir()):
            if not p.is_dir() or not any(p.glob("*.pdf")):
                continue
            gt = json.loads((p / "ground_truth.json").read_text()) if (p / "ground_truth.json").exists() else {}
            out.append({"id": p.name, "kind": kind, "files": sorted(f.name for f in p.glob("*.pdf")),
                        "case_type": gt.get("case_type"), "vendor": gt.get("vendor"),
                        "expected": gt.get("expected_recommendation"),
                        "indexed": {path: (INDEX / path / p.name / "build.json").exists() for path in ("A", "B")}})
    return out


@app.post("/api/packages")
async def upload(name: str = Form(...), files: list[UploadFile] = File(...)):
    target = UPLOADS / _safe(name)
    if (PACKAGES / name).exists():
        raise HTTPException(400, "name clashes with a benchmark package")
    shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True)
    for f in files:
        fname = Path(f.filename or "").name
        if not fname.lower().endswith(".pdf"):
            continue
        (target / _safe(fname)).write_bytes(await f.read())
    for path in ("A", "B"):  # stale indexes from a previous upload under the same name
        shutil.rmtree(INDEX / path / name, ignore_errors=True)
    return {"id": name, "files": sorted(f.name for f in target.glob("*.pdf"))}


@app.get("/api/packages/{pkg}/files/{fname}")
def package_file(pkg: str, fname: str):
    f = _package_dir(pkg) / _safe(fname)
    if not f.exists() or f.suffix.lower() != ".pdf":
        raise HTTPException(404)
    return FileResponse(f, media_type="application/pdf", headers={"Content-Disposition": f'inline; filename="{fname}"'})


# ------------------------------------------------------------------ verification jobs (single worker)

JOBS: dict[str, dict] = {}
QUEUE: "queue.Queue[str]" = queue.Queue()
LOCK = threading.Lock()


class JobIn(BaseModel):
    package: str
    path: str
    assisted: bool = False


class BatchIn(BaseModel):
    packages: list[str]
    paths: list[str] = ["A", "B"]
    assisted: bool = False


def _worker():
    while True:
        jid = QUEUE.get()
        job = JOBS[jid]
        try:
            pdir = _package_dir(job["package"])
            job.update(status="running", stage="Extracting documents & building index",
                       started_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            pipeline.prepare(pdir, job["path"], INDEX)
            job["stage"] = "Agent verifying"

            def on_step(step):
                with LOCK:
                    job["steps"].append(asdict(step))

            run, vid = pipeline.verify(pdir, job["path"], INDEX, WRITER, extra={"source": "app"}, on_step=on_step,
                                       assisted=job.get("assisted", False))
            job.update(status="done", stage="Saved as PENDING_REVIEW", verification_id=vid,
                       recommendation=run.recommendation.label if run.recommendation else None, run_status=run.status.value)
        except Exception as e:  # surfaced to the UI
            job.update(status="error", stage="Failed", error=f"{type(e).__name__}: {e}")
        finally:
            QUEUE.task_done()


threading.Thread(target=_worker, daemon=True).start()


def _enqueue(package: str, path: str, assisted: bool) -> dict:
    if path not in ("A", "B"):
        raise HTTPException(400, "path must be A or B")
    _package_dir(package)
    jid = uuid.uuid4().hex[:10]
    JOBS[jid] = {"id": jid, "package": package, "path": path, "assisted": assisted, "status": "queued", "stage": "Queued",
                 "steps": [], "created_at": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
    QUEUE.put(jid)
    return JOBS[jid]


@app.post("/api/jobs")
def create_job(body: JobIn):
    return _enqueue(body.package, body.path, body.assisted)


@app.post("/api/jobs/batch")
def create_batch(body: BatchIn):
    """Queue many verifications; the single worker runs them one after another (e.g. overnight)."""
    return [_enqueue(p, path, body.assisted) for p in body.packages for path in body.paths]


@app.get("/api/queue")
def queue_status():
    counts: dict[str, int] = {}
    for j in JOBS.values():
        counts[j["status"]] = counts.get(j["status"], 0) + 1
    return counts


@app.get("/api/jobs")
def jobs():
    return [dict(j, steps=[]) for j in sorted(JOBS.values(), key=lambda j: j["created_at"], reverse=True)[:60]]


@app.get("/api/jobs/{jid}")
def job(jid: str):
    if jid not in JOBS:
        raise HTTPException(404)
    with LOCK:
        return dict(JOBS[jid], steps=list(JOBS[jid]["steps"]))


# ------------------------------------------------------------------ benchmark results

@app.get("/api/benchmarks")
def benchmarks():
    return [d.name for d in sorted(RESULTS.iterdir()) if (d / "summary.json").exists()] if RESULTS.exists() else []


@app.get("/api/benchmarks/{tag}")
def benchmark(tag: str):
    d = RESULTS / _safe(tag)
    if not (d / "summary.json").exists():
        raise HTTPException(404)
    runs = list(csv.DictReader((d / "runs.csv").open())) if (d / "runs.csv").exists() else []
    manifest = json.loads((d / "manifest.json").read_text()) if (d / "manifest.json").exists() else {}
    return {"summary": json.loads((d / "summary.json").read_text()), "runs": runs, "manifest": manifest}
