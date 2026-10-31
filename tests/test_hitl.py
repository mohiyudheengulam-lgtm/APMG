"""HITL gate (Exposé §6.5 step 7): no final decision is written before the approval function is called."""

import json
import sqlite3
from decimal import Decimal

import pytest

from agent_on_duty.agent.react import AgentRun, RunStatus
from agent_on_duty.audit.store import RecommendationWriter, approve, connect, decisions_without_signoff
from agent_on_duty.schemas import Decision, Finding, Flag, Recommendation, SourceRef


def _run() -> AgentRun:
    rec = Recommendation(package_id="PKG-X", findings=[
        Finding(flag=Flag.SURCHARGE, amount=Decimal(150), evidence=[SourceRef(document="MSA.pdf", page=14)])])
    return AgentRun(package_id="PKG-X", path="B", recommendation=rec, status=RunStatus.FINISHED)


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "aod.sqlite"
    return db, RecommendationWriter(db, tmp_path / "audit")


def test_saved_as_pending_without_decision(store):
    db, writer = store
    vid = writer.save(_run())
    with connect(db) as con:
        assert con.execute("SELECT review_state FROM verifications WHERE id=?", (vid,)).fetchone()[0] == "PENDING_REVIEW"
        assert con.execute("SELECT count(*) FROM decisions").fetchone()[0] == 0


def test_writer_has_no_decision_method(store):
    _, writer = store
    assert not any(hasattr(writer, m) for m in ("approve", "decide", "reject", "set_decision"))


def test_db_rejects_reviewed_without_decision(store):
    db, writer = store
    vid = writer.save(_run())
    with pytest.raises(sqlite3.IntegrityError, match="no manager decision"), connect(db) as con:
        con.execute("UPDATE verifications SET review_state='REVIEWED' WHERE id=?", (vid,))
    with pytest.raises(sqlite3.IntegrityError, match="PENDING_REVIEW"), connect(db) as con:
        con.execute("INSERT INTO verifications (id, package_id, path, created_at, run_status, review_state, audit_path) "
                    "VALUES ('x', 'p', 'A', 'now', 'finished', 'REVIEWED', 'a.json')")


def test_approve_records_decision_and_audit(store, tmp_path):
    db, writer = store
    vid = writer.save(_run())
    with pytest.raises(ValueError):
        approve(db, vid, Decision.OVERRIDDEN, "manager", override_reason=" ")
    approve(db, vid, Decision.OVERRIDDEN, "manager", override_reason="surcharge approved by email 2026-10-01")
    audit = json.loads((tmp_path / "audit" / f"{vid}.json").read_text())
    assert audit["review_state"] == "REVIEWED"
    assert audit["manager_decision"]["decision"] == "OVERRIDDEN"
    assert audit["recommendation"] == "FLAGGED_SURCHARGE"
    assert decisions_without_signoff(db) == 0
    with pytest.raises(ValueError, match="already reviewed"):
        approve(db, vid, Decision.APPROVED, "manager")
