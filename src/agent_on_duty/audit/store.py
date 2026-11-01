"""Local action and audit engine + HITL gate (Exposé §4, §5.4, §5.5).

- RecommendationWriter: the only handle the agent pipeline gets. It can store a recommendation as
  PENDING_REVIEW and write the JSON audit record. It has no method that writes a decision.
- approve(): the manager approval function, the only writer of final decisions.
- SQLite triggers enforce the same rule at the database level: a verification can only be inserted as
  PENDING_REVIEW, and it can only become REVIEWED once a decision row exists.
"""

import json
import sqlite3
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from agent_on_duty.agent.react import MAX_STEPS, MODEL, RUN_OPTIONS, THINK, AgentRun
from agent_on_duty.schemas import Decision, ManagerDecision, ReviewState

SCHEMA = """
CREATE TABLE IF NOT EXISTS verifications (
    id TEXT PRIMARY KEY,
    package_id TEXT NOT NULL,
    path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    run_status TEXT NOT NULL,
    recommendation TEXT,          -- NO_DISCREPANCY / FLAGGED_* list / NULL when the run produced none
    recommendation_json TEXT,
    review_state TEXT NOT NULL DEFAULT 'PENDING_REVIEW',
    audit_path TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS decisions (
    verification_id TEXT PRIMARY KEY REFERENCES verifications(id),
    decision TEXT NOT NULL CHECK (decision IN ('APPROVED', 'REJECTED', 'OVERRIDDEN')),
    reviewer TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    override_reason TEXT,
    CHECK (decision != 'OVERRIDDEN' OR length(trim(coalesce(override_reason, ''))) > 0)
);
CREATE TRIGGER IF NOT EXISTS verification_starts_pending
BEFORE INSERT ON verifications WHEN NEW.review_state != 'PENDING_REVIEW'
BEGIN SELECT RAISE(ABORT, 'verifications must be created as PENDING_REVIEW'); END;
CREATE TRIGGER IF NOT EXISTS reviewed_requires_decision
BEFORE UPDATE OF review_state ON verifications
WHEN NEW.review_state = 'REVIEWED' AND NOT EXISTS (SELECT 1 FROM decisions WHERE verification_id = NEW.id)
BEGIN SELECT RAISE(ABORT, 'no manager decision recorded'); END;
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    return con


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def audit_record(run: AgentRun, verification_id: str) -> dict:
    rec = run.recommendation
    return {
        "verification_id": verification_id,
        "package_id": run.package_id,
        "retrieval_path": run.path,
        "model_settings": {"model": MODEL, **RUN_OPTIONS, "think": THINK, "max_steps": MAX_STEPS},
        "mode": run.mode,
        "extraction_check": run.extraction_check,
        "notes": run.notes,
        "compactions": run.compactions,
        "run_status": run.status.value,
        "seconds_total": run.seconds,
        "prompt_tokens_total": run.prompt_tokens,
        "output_tokens_total": sum(s.output_tokens for s in run.steps),
        "steps": [asdict(s) for s in run.steps],
        "invalid_tool_calls": run.invalid_tool_calls,
        "submitted_values": run.submitted,
        "calculations": run.calculations,
        "cited_clauses": run.cited_clauses,
        "recommendation": rec.label if rec else None,
        "findings": json.loads(rec.model_dump_json())["findings"] if rec else None,
        "review_state": ReviewState.PENDING_REVIEW.value,
        "manager_decision": None,
    }


class RecommendationWriter:
    """Handed to the verification pipeline. Can only create PENDING_REVIEW entries."""

    def __init__(self, db_path: Path, audit_dir: Path):
        self.db_path, self.audit_dir = db_path, audit_dir

    def save(self, run: AgentRun, extra: dict | None = None) -> str:
        vid = uuid.uuid4().hex[:12]
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        audit_path = self.audit_dir / f"{vid}.json"
        record = audit_record(run, vid) | (extra or {})
        audit_path.write_text(json.dumps(record, indent=1, default=str))
        with connect(self.db_path) as con:
            con.execute(
                "INSERT INTO verifications (id, package_id, path, created_at, run_status, recommendation, "
                "recommendation_json, audit_path) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (vid, run.package_id, run.path, _now(), run.status.value, record["recommendation"],
                 run.recommendation.model_dump_json() if run.recommendation else None, str(audit_path)),
            )
        return vid


def approve(db_path: Path, verification_id: str, decision: Decision, reviewer: str,
            override_reason: str | None = None) -> ManagerDecision:
    """Manager approval function — the only code path that records a final decision."""
    if decision == Decision.OVERRIDDEN and not (override_reason or "").strip():
        raise ValueError("an override needs a written reason")
    md = ManagerDecision(decision=decision, reviewer=reviewer, timestamp=datetime.now(timezone.utc),
                         override_reason=override_reason)
    with connect(db_path) as con:
        row = con.execute("SELECT audit_path, review_state FROM verifications WHERE id = ?", (verification_id,)).fetchone()
        if row is None:
            raise KeyError(verification_id)
        if row["review_state"] == ReviewState.REVIEWED:
            raise ValueError("already reviewed")
        con.execute("INSERT INTO decisions VALUES (?, ?, ?, ?, ?)",
                    (verification_id, md.decision.value, md.reviewer, md.timestamp.isoformat(), md.override_reason))
        con.execute("UPDATE verifications SET review_state = 'REVIEWED' WHERE id = ?", (verification_id,))
    audit_path = Path(row["audit_path"])
    record = json.loads(audit_path.read_text())
    record["review_state"] = ReviewState.REVIEWED.value
    record["manager_decision"] = json.loads(md.model_dump_json())
    audit_path.write_text(json.dumps(record, indent=1, default=str))
    return md


def list_verifications(db_path: Path) -> list[dict]:
    with connect(db_path) as con:
        rows = con.execute(
            "SELECT v.*, d.decision, d.reviewer, d.timestamp AS decided_at, d.override_reason "
            "FROM verifications v LEFT JOIN decisions d ON d.verification_id = v.id ORDER BY v.created_at DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def decisions_without_signoff(db_path: Path) -> int:
    """Criterion 5 governance check: REVIEWED entries lacking a decision, plus decisions without reviewer. Expected 0."""
    with connect(db_path) as con:
        return con.execute(
            "SELECT (SELECT count(*) FROM verifications v WHERE review_state = 'REVIEWED' "
            "        AND NOT EXISTS (SELECT 1 FROM decisions d WHERE d.verification_id = v.id))"
            " + (SELECT count(*) FROM decisions WHERE trim(reviewer) = '')"
        ).fetchone()[0]
