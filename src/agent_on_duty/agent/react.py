"""Single ReAct agent (Exposé §5.3), identical for both paths; only the retrieval tool differs.

The model reads documents through the active retrieval path, submits the values it extracted,
and calls deterministic tools for every calculation. Its only output is a Recommendation —
it has no access to the decision store (§5.4).
"""

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Literal

import ollama
from pydantic import BaseModel, Field, ValidationError

from agent_on_duty.retrieval.path_a import PathAIndex
from agent_on_duty.retrieval.path_b import PathBBundle
from agent_on_duty.schemas import (
    Finding, Flag, GoodsReceipt, Invoice, LineItem, PurchaseOrder, Recommendation, SourceRef, Surcharge,
)
from agent_on_duty.tools.calc import line_total_variance, price_variance, quantity_variance

MODEL = "qwen3:1.7b"
RUN_OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 16384}
THINK = False
MAX_STEPS = 10

SYSTEM_PROMPT = """You are an accounts-payable verification agent. Check one procurement package.
A package normally contains: an invoice, a purchase order (PO), a delivery note, a goods receipt (the buyer's
record of the quantities actually received), the master supply agreement with the supplier (MSA), and the buyer's
purchasing guideline.

You have at most 10 turns, so call several tools per turn: retrieve all documents in one turn,
submit all documents in one turn together with run_checks.

Procedure:
1. Find the invoice, the purchase order and the goods receipt with the retrieval tool.
2. Read each document BEFORE submitting it. Then call submit_document with the exact values you read:
   the source PDF filename shown with the retrieved text, and every line item (item_no, quantity, unit_price,
   line_total). For the goods receipt submit item_no and the quantity RECEIVED.
   Invoice lines without an item number that are additional charges (e.g. freight, fuel, energy, handling or
   small-quantity surcharges or fees) are surcharges: submit them under surcharges, not as line items.
   VAT is a tax, not a surcharge.
   If a document cannot be found, call report_missing instead. Never invent values.
3. Call run_checks. It computes all price, quantity and line-total differences. Do not do arithmetic yourself.
4. If the invoice has a surcharge, find the MSA clause about surcharges, read it, and call check_surcharge
   with the clause's source PDF filename and the page number where the clause text appears. Set allowed=true
   only if the clause explicitly permits this kind of surcharge and its amount without further approval;
   otherwise allowed=false.
5. Call finish.
Submitting a document or clause you have not retrieved yet is rejected. Answer only with tool calls."""


# ------------------------------------------------------------------ tool argument schemas

class LineArg(BaseModel):
    item_no: str
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal | None = None
    line_total: Decimal | None = None


class SurchargeArg(BaseModel):
    label: str
    amount: Decimal


class SubmitDocumentArgs(BaseModel):
    doc_type: Literal["invoice", "purchase_order", "goods_receipt"]
    document: str
    lines: list[LineArg] = Field(min_length=1)
    surcharges: list[SurchargeArg] = []


class ReportMissingArgs(BaseModel):
    doc_type: Literal["invoice", "purchase_order", "goods_receipt"]


class CheckSurchargeArgs(BaseModel):
    label: str
    amount: Decimal
    allowed: bool
    clause_document: str
    clause_page: int = Field(ge=1)
    reason: str


class SearchArgs(BaseModel):
    query: str


class ReadArgs(BaseModel):
    paths: list[str] | str = Field(default_factory=list)
    path: list[str] | str | None = None  # models use either field, with one path or a list

    def all_paths(self) -> list[str]:
        as_list = lambda v: [v] if isinstance(v, str) else list(v or [])  # noqa: E731
        out = as_list(self.paths) + as_list(self.path)
        if not out:
            raise ValueError("give 'paths' (up to 5 files)")
        return out[:5]


def _tool(name: str, description: str, model: type[BaseModel]) -> dict:
    schema = model.model_json_schema()
    return {"type": "function", "function": {"name": name, "description": description, "parameters": schema}}


COMMON_TOOLS = [
    _tool("submit_document", "Submit the values you extracted from one document.", SubmitDocumentArgs),
    _tool("report_missing", "Report that a required document is not in the package.", ReportMissingArgs),
    _tool("run_checks", "Run deterministic price, quantity and line-total checks on the submitted documents.",
          type("NoArgs", (BaseModel,), {})),
    _tool("check_surcharge", "Record whether an invoice surcharge is allowed by the cited MSA clause.", CheckSurchargeArgs),
    _tool("finish", "Finish verification and return the recommendation.", type("NoArgs", (BaseModel,), {})),
]


# ------------------------------------------------------------------ retrieval adapters (the treatment)

class PathATools:
    name = "A"
    tools = [_tool("search", "Semantic search over all package documents. Returns the 5 most similar text chunks "
                   "with their document and page.", SearchArgs)]

    def __init__(self, index: PathAIndex):
        self.index = index

    def call(self, name: str, args: dict) -> tuple[str, set[tuple[str, int]]]:
        chunks = self.index.search(SearchArgs(**args).query)
        text = "\n\n".join(f"[source: {c.document} page {c.page}]\n{c.text}" for c in chunks)
        return text, {(c.document, c.page) for c in chunks}


class PathBTools:
    name = "B"
    tools = [_tool("read", "Open up to 5 files of the package knowledge bundle at once. Files: 'index.md' "
                   "(package overview), 'invoice.md', 'purchase_order.md', 'delivery_note.md', 'goods_receipt.md', "
                   "'guideline.md', 'msa/index.md' (list of contract sections) and the 'msa/...' section files linked "
                   "from it. Use full paths like 'msa/index.md'.", ReadArgs)]

    def __init__(self, bundle: PathBBundle):
        self.bundle = bundle

    def call(self, name: str, args: dict) -> tuple[str, set[tuple[str, int]]]:
        texts, seen = [], set()
        for path in ReadArgs(**args).all_paths():
            try:
                text, meta = self.bundle.read(path), self.bundle.meta(path)
            except (FileNotFoundError, ValueError):
                texts.append(f"=== {path} ===\nError: no such file")
                continue
            pages = meta.get("pages") or ([meta["page"]] if "page" in meta else [])
            if "source_document" in meta:
                seen |= {(meta["source_document"], int(pg)) for pg in pages}
            texts.append(f"=== {path} ===\n{text}")
        if not seen and all(t.endswith("Error: no such file") for t in texts):
            raise FileNotFoundError(", ".join(ReadArgs(**args).all_paths()))
        return "\n\n".join(texts), seen


# ------------------------------------------------------------------ run state

class RunStatus(StrEnum):
    FINISHED = "finished"
    STEP_LIMIT = "step_limit"
    ERROR = "error"


@dataclass
class Step:
    step: int
    tool_calls: list[dict]
    prompt_tokens: int
    output_tokens: int
    seconds: float
    content: str = ""


@dataclass
class AgentRun:
    package_id: str
    path: str
    steps: list[Step] = field(default_factory=list)
    invalid_tool_calls: int = 0
    calculations: list[dict] = field(default_factory=list)
    cited_clauses: list[dict] = field(default_factory=list)
    submitted: dict[str, dict] = field(default_factory=dict)
    recommendation: Recommendation | None = None
    status: RunStatus = RunStatus.ERROR
    seconds: float = 0.0
    mode: str = "research"   # "assisted": documents pre-submitted from extraction (never used in the benchmark)
    compactions: int = 0     # retrieval results replaced by a one-line note to keep the context small

    @property
    def prompt_tokens(self) -> int:
        return sum(s.prompt_tokens for s in self.steps)


COMPACT_AFTER_STEPS = 3


class Verifier:
    def __init__(self, package_id: str, retrieval: PathATools | PathBTools, documents: list[dict] | None = None,
                 assisted=None):
        """`assisted`: an ExtractedPackage — invoice, PO and goods receipt are submitted from extraction and checked
        before the agent starts; the agent only handles MSA clauses. Not part of the research comparison."""
        self.retrieval = retrieval
        self.documents = documents or []
        self.run = AgentRun(package_id=package_id, path=retrieval.name)
        self.docs: dict[str, PurchaseOrder | GoodsReceipt | Invoice] = {}
        self.missing: set[str] = set()
        self.findings: list[Finding] = []
        self.surcharge_findings: list[Finding] = []
        self.seen: set[tuple[str, int]] = set()  # (document, page) revealed by retrieval so far
        self.checks_ran = False
        self.done = False
        self._last_seen: set[tuple[str, int]] = set()
        self.precheck = ""
        if assisted is not None:
            self._preload(assisted)

    def _preload(self, pkg):
        from agent_on_duty.extraction.extract import DocType  # local import: extraction is optional here
        self.run.mode = "assisted"
        for key in ("invoice", "purchase_order", "goods_receipt"):
            doc = pkg.get(DocType(key))
            if doc is None or doc.record is None:
                self.missing.add(key)
                continue
            self.docs[key] = doc.record
            self.seen.add((doc.filename, 1))
            self.run.submitted[key] = {"doc_type": key, "document": doc.filename,
                                       "lines": [{"item_no": ln.item_no, "quantity": str(ln.quantity),
                                                  "unit_price": None if ln.unit_price is None else str(ln.unit_price),
                                                  "line_total": None if ln.line_total is None else str(ln.line_total)}
                                                 for ln in doc.record.lines],
                                       "surcharges": [{"label": sc.label, "amount": str(sc.amount)}
                                                      for sc in getattr(doc.record, "surcharges", [])]}
        self.precheck = self.run_checks() if "invoice" in self.docs else "No invoice found."

    def _require_seen(self, document: str, page: int | None = None):
        if not any(d == document and (page is None or p == page) for d, p in self.seen):
            where = f"{document}" + (f" page {page}" if page else "")
            raise ValueError(f"{where} has not been retrieved yet; retrieve it first and use its source filename")

    # -------------------------------------------------- tools
    def submit_document(self, a: SubmitDocumentArgs) -> str:
        self._require_seen(a.document)
        ref = SourceRef(document=a.document, page=1)
        lines = [LineItem(item_no=ln.item_no, description="", quantity=ln.quantity, unit_price=ln.unit_price,
                          line_total=ln.line_total, source=ref) for ln in a.lines]
        if a.doc_type == "invoice":
            self.docs["invoice"] = Invoice(invoice_number=a.document, po_number="", vendor="", lines=lines, source=ref,
                                           surcharges=[Surcharge(label=s.label, amount=s.amount, source=ref) for s in a.surcharges])
        elif a.doc_type == "purchase_order":
            self.docs["purchase_order"] = PurchaseOrder(po_number=a.document, vendor="", lines=lines, source=ref)
        else:
            self.docs["goods_receipt"] = GoodsReceipt(receipt_number=a.document, po_number="", lines=lines, source=ref)
        self.run.submitted[a.doc_type] = json.loads(a.model_dump_json())
        return f"{a.doc_type} recorded with {len(lines)} line(s)."

    def report_missing(self, a: ReportMissingArgs) -> str:
        self.missing.add(a.doc_type)
        return f"{a.doc_type} recorded as missing."

    def run_checks(self) -> str:
        inv, po, gr = (self.docs.get(k) for k in ("invoice", "purchase_order", "goods_receipt"))
        if inv is None:
            return "Error: submit the invoice first."
        findings = line_total_variance(inv)
        if po:
            findings += price_variance(po, inv)
        if po and gr:
            findings += quantity_variance(po, gr, inv)
        self.findings = findings
        self.checks_ran = True
        for f in findings:
            self.run.calculations.append(json.loads(f.model_dump_json()))
        skipped = [k for k in ("purchase_order", "goods_receipt") if k not in self.docs]
        lines = [f"{f.flag} item {f.item_no}: expected {f.expected}, got {f.actual}, impact {f.amount} ({f.formula})"
                 for f in findings] or ["No price, quantity or line-total differences."]
        if skipped:
            lines.append(f"Not checked because not submitted: {', '.join(skipped)}.")
        if inv.surcharges:
            lines.append("Invoice has surcharges: " + ", ".join(f"{s.label} {s.amount}" for s in inv.surcharges)
                         + ". Check them against the MSA.")
        return "\n".join(lines)

    def check_surcharge(self, a: CheckSurchargeArgs) -> str:
        self._require_seen(a.clause_document, a.clause_page)
        clause = SourceRef(document=a.clause_document, page=a.clause_page)
        self.run.cited_clauses = [c for c in self.run.cited_clauses if c["label"] != a.label]
        self.surcharge_findings = [f for f in self.surcharge_findings if not (f.formula or "").startswith(f"{a.label} ")]
        self.run.cited_clauses.append({"label": a.label, "document": a.clause_document, "page": a.clause_page,
                                       "allowed": a.allowed, "reason": a.reason})
        if not a.allowed:
            inv = self.docs.get("invoice")
            evidence = [inv.source, clause] if inv else [clause]
            self.surcharge_findings.append(Finding(flag=Flag.SURCHARGE, amount=a.amount, evidence=evidence,
                                                   formula=f"{a.label} not permitted: {a.reason}"))
        return "Recorded."

    def finish(self) -> str:
        if not self.checks_ran and "invoice" not in self.missing:
            raise ValueError("run_checks has not completed; submit the documents and call run_checks first")
        findings = list(self.findings) + self.surcharge_findings
        for doc_type in sorted(self.missing):
            findings.append(Finding(flag=Flag.MISSING_DOCUMENT, formula=f"{doc_type} not found in package",
                                    evidence=[SourceRef(document=self.run.package_id, page=1)]))
        self.run.recommendation = Recommendation(package_id=self.run.package_id, findings=findings)
        self.done = True
        return "Done."

    # -------------------------------------------------- dispatch
    def dispatch(self, name: str, args: dict) -> str:
        try:
            if name in {t["function"]["name"] for t in self.retrieval.tools}:
                text, seen = self.retrieval.call(name, args)
                self.seen |= seen
                self._last_seen = seen
                return text
            match name:
                case "submit_document":
                    return self.submit_document(SubmitDocumentArgs(**args))
                case "report_missing":
                    return self.report_missing(ReportMissingArgs(**args))
                case "check_surcharge":
                    return self.check_surcharge(CheckSurchargeArgs(**args))
                case "run_checks":
                    return self.run_checks()
                case "finish":
                    return self.finish()
            raise ValueError(f"unknown tool {name}")
        except (ValidationError, ValueError, FileNotFoundError, TypeError) as e:
            self.run.invalid_tool_calls += 1
            return f"Error: invalid call to {name}: {str(e)[:400]}"

    def _task(self) -> str:
        """First message — identical for both paths: the package's files and their detected document types."""
        lines = [f"Verify package {self.run.package_id}."]
        if self.documents:
            lines.append("Documents in this package:")
            lines += [f"- {d['file']} ({d['type'].replace('_', ' ')})" for d in self.documents]
        if self.run.mode == "assisted":
            lines += ["", "The invoice, purchase order and goods receipt were already extracted, submitted and checked:",
                      self.precheck,
                      "Missing: " + (", ".join(sorted(self.missing)) if self.missing else "none") + ".",
                      "Remaining task: if the invoice has surcharges, retrieve the MSA surcharge clause and call "
                      "check_surcharge; for missing documents call report_missing; then call finish."]
        return "\n".join(lines)

    def _consumed(self) -> set[str]:
        """Documents whose content the agent has already turned into submissions or citations."""
        return {v["document"] for v in self.run.submitted.values()} | {c["document"] for c in self.run.cited_clauses}

    def _compact(self, messages: list[dict], retrieved: list[dict], step: int):
        """Replace old or fully used retrieval results with a one-line note (same rule for both paths)."""
        consumed = self._consumed()
        for r in retrieved:
            if r["compacted"]:
                continue
            docs = {d for d, _ in r["seen"]}
            if (docs and docs <= consumed) or step - r["step"] >= COMPACT_AFTER_STEPS:
                where = ", ".join(f"{d} p.{p}" for d, p in sorted(r["seen"])) or "nothing citable"
                messages[r["index"]]["content"] = (f"[Earlier {r['tool']} result for {r['args']} removed to keep the context "
                                                   f"small ({where}). Retrieve it again if you still need it.]")
                r["compacted"] = True
                self.run.compactions += 1

    def verify(self, client: ollama.Client | None = None, on_step: Callable[[Step], None] | None = None) -> AgentRun:
        client = client or ollama.Client()
        tools = self.retrieval.tools + COMMON_TOOLS
        messages = [{"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": self._task()}]
        retrieval_tools = {t["function"]["name"] for t in self.retrieval.tools}
        retrieved: list[dict] = []
        t_start = time.perf_counter()
        try:
            for step in range(1, MAX_STEPS + 1):
                t0 = time.perf_counter()
                resp = client.chat(model=MODEL, messages=messages, tools=tools, options=RUN_OPTIONS, think=THINK)
                msg = resp.message
                calls = msg.tool_calls or []
                messages.append(msg.model_dump(exclude_none=True))
                record = Step(step=step, tool_calls=[], prompt_tokens=resp.prompt_eval_count or 0,
                              output_tokens=resp.eval_count or 0, seconds=0.0, content=(msg.content or "")[:500])
                if not calls:
                    messages.append({"role": "user", "content": "Continue the procedure using tool calls. Call finish when done."})
                for c in calls:
                    args = dict(c.function.arguments or {})
                    result = self.dispatch(c.function.name, args)
                    record.tool_calls.append({"name": c.function.name, "arguments": args, "result": result[:4000]})
                    messages.append({"role": "tool", "tool_name": c.function.name, "content": result})
                    if c.function.name in retrieval_tools and not result.startswith("Error"):
                        retrieved.append({"index": len(messages) - 1, "step": step, "tool": c.function.name,
                                          "args": json.dumps(args)[:120], "seen": set(self._last_seen), "compacted": False})
                self._compact(messages, retrieved, step)
                record.seconds = round(time.perf_counter() - t0, 3)
                self.run.steps.append(record)
                if on_step:
                    on_step(record)
                if self.done:
                    self.run.status = RunStatus.FINISHED
                    break
            else:
                self.run.status = RunStatus.STEP_LIMIT
        except Exception as e:  # model server errors etc. — recorded, never crash the benchmark
            self.run.status = RunStatus.ERROR
            self.run.steps.append(Step(step=len(self.run.steps) + 1, tool_calls=[], prompt_tokens=0, output_tokens=0,
                                       seconds=0, content=f"{type(e).__name__}: {e}"))
        self.run.seconds = round(time.perf_counter() - t_start, 3)
        return self.run
