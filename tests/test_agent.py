"""Agent loop with a scripted model (no LLM): recommendation, guards, context compaction, assisted mode."""

import json

from ollama import ChatResponse, Message

from agent_on_duty.agent.react import PathBTools, RunStatus, Verifier
from agent_on_duty.extraction.extract import extract_package
from agent_on_duty.retrieval import path_b
from agent_on_duty.retrieval.path_b import PathBBundle


class ScriptedModel:
    """Plays back one list of tool calls per turn and records the messages it was sent."""

    def __init__(self, turns):
        self.turns, self.seen_messages = list(turns), []

    def chat(self, messages, **_):
        self.seen_messages.append([dict(m) for m in messages])
        calls = [Message.ToolCall(function=Message.ToolCall.Function(name=n, arguments=a)) for n, a in self.turns.pop(0)]
        return ChatResponse(message=Message(role="assistant", content="", tool_calls=calls), prompt_eval_count=1, eval_count=1)


def _combined(packages):
    pdir = next(p for p in packages if json.loads((p / "ground_truth.json").read_text())["case_type"] == "combined")
    return pdir, json.loads((pdir / "ground_truth.json").read_text())


def _submit(gt, doc_type):
    f = gt["fields"][doc_type]
    args = {"doc_type": doc_type, "document": gt["documents"][doc_type], "lines": f["lines"]}
    if doc_type == "invoice":
        args["surcharges"] = f["surcharges"]
    return ("submit_document", args)


def _bundle(pdir, tmp_path):
    path_b.convert(pdir, tmp_path / "B")
    return PathBTools(PathBBundle(tmp_path / "B"))


def _surcharge_file(tools):
    return next(f.name for f in (tools.bundle.root / "msa").iterdir() if "surcharge" in f.name)


def test_research_mode_finds_all_flags_and_compacts(packages, tmp_path):
    pdir, gt = _combined(packages)
    tools = _bundle(pdir, tmp_path)
    clause = gt["msa_clauses"]["surcharges"]
    sc = gt["fields"]["invoice"]["surcharges"][0]
    model = ScriptedModel([
        [("read", {"path": ["invoice.md", "purchase_order.md", "goods_receipt.md"]})],
        [_submit(gt, "invoice"), _submit(gt, "purchase_order"), _submit(gt, "goods_receipt"), ("run_checks", {})],
        [("read", {"paths": [f"msa/{_surcharge_file(tools)}"]})],
        [("check_surcharge", {"label": sc["label"], "amount": sc["amount"], "allowed": False,
                              "clause_document": clause["document"], "clause_page": clause["page"], "reason": "not pre-approved"})],
        [("finish", {})],
    ])
    run = Verifier(pdir.name, tools).verify(client=model)
    assert run.status == RunStatus.FINISHED and run.invalid_tool_calls == 0
    assert run.recommendation.label == gt["expected_recommendation"]
    # after submission the first read result (invoice/PO/GR) is replaced by a note in later turns
    assert run.compactions >= 1
    later = model.seen_messages[2]
    first_read = next(m for m in later if m.get("role") == "tool")
    assert first_read["content"].startswith("[Earlier read result")


def test_unretrieved_values_are_rejected(packages, tmp_path):
    pdir, gt = _combined(packages)
    model = ScriptedModel([[_submit(gt, "invoice")], [("finish", {})]] + [[("finish", {})]] * 8)
    run = Verifier(pdir.name, _bundle(pdir, tmp_path)).verify(client=model)
    assert run.invalid_tool_calls >= 2 and run.recommendation is None


def test_assisted_mode_only_needs_the_msa(packages, tmp_path):
    pdir, gt = _combined(packages)
    tools = _bundle(pdir, tmp_path)
    clause = gt["msa_clauses"]["surcharges"]
    sc = gt["fields"]["invoice"]["surcharges"][0]
    model = ScriptedModel([
        [("read", {"path": f"msa/{_surcharge_file(tools)}"})],
        [("check_surcharge", {"label": sc["label"], "amount": sc["amount"], "allowed": False,
                              "clause_document": clause["document"], "clause_page": clause["page"], "reason": "x"})],
        [("finish", {})],
    ])
    run = Verifier(pdir.name, tools, assisted=extract_package(pdir)).verify(client=model)
    assert run.mode == "assisted" and run.status == RunStatus.FINISHED
    assert run.recommendation.label == gt["expected_recommendation"]
    assert "were already extracted" in model.seen_messages[0][1]["content"]
