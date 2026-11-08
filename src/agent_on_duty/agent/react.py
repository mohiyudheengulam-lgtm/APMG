"""Single ReAct agent (Exposé §5.3), identical for both paths; only the retrieval tool differs.

The model reads documents through the active retrieval path, submits the values it extracted,
and calls deterministic tools for every calculation. Its only output is a Recommendation —
it has no access to the decision store (§5.4).
"""

import json
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum
from typing import Annotated, Literal

import ollama
from pydantic import BaseModel, BeforeValidator, Field, ValidationError, model_validator

from agent_on_duty.retrieval.path_a import PathAIndex
from agent_on_duty.retrieval.path_b import PathBBundle
from agent_on_duty.schemas import (
    Finding, Flag, GoodsReceipt, Invoice, LineItem, PurchaseOrder, Recommendation, SourceRef, Surcharge,
)
from agent_on_duty.tools.calc import line_total_variance, price_variance, quantity_variance, unmatched_lines

MODEL = "qwen3:1.7b"
RUN_OPTIONS = {"temperature": 0, "seed": 42, "num_ctx": 16384}
THINK = False
MAX_STEPS = 10

_SYSTEM_PROMPT_BASE = """You are an accounts-payable verification agent. Check one procurement package.
A package normally contains: an invoice, a purchase order (PO), a delivery note, a goods receipt (the buyer's
record of the quantities actually received), the master supply agreement with the supplier (MSA), and the buyer's
purchasing guideline.

You have at most 10 turns. Call several tools per turn where they do not depend on each other.

Procedure:
1. {retrieval_step}
2. After the retrieved text has been returned to you, call submit_document for each document with the values
   shown in it. Use the exact source filename shown next to [source: ...] in the retrieved text.
   Submit every line item with its item_no, quantity, unit_price, and line_total exactly as printed.
   item_no is the article number from the item column of the document, not the position number (Pos.).
   For the goods receipt: submit item_no and the quantity RECEIVED only (no price).
   Invoice lines without an article number that are additional charges (e.g. freight, fuel, energy, handling or
   small-quantity surcharges or fees) are surcharges: submit them under surcharges, not as line items.
   VAT is a tax, not a surcharge. If a document is missing, call report_missing instead. Never invent values.
3. Call run_checks immediately after submitting all three documents.
4. If the invoice has surcharges: retrieve the MSA surcharge clause, then call check_surcharge with the clause
   filename and page number. Set allowed=true only if the clause explicitly pre-approves this surcharge type.
5. Call finish.
Never output plain text. Every response must contain at least one tool call."""

_PATH_A_RETRIEVAL = ("Use `search` to retrieve the invoice, purchase order, and goods receipt: one search per "
                     "document, with words you expect in it. If the results do not show that document's line items, "
                     "search again with different words. Search is by meaning: filenames do not find documents.")

_PATH_B_RETRIEVAL = ("Use `read` with paths=['invoice.md', 'purchase_order.md', 'goods_receipt.md'] "
                     "to open all three at once.")

SYSTEM_PROMPT_A = _SYSTEM_PROMPT_BASE.format(retrieval_step=_PATH_A_RETRIEVAL)
SYSTEM_PROMPT_B = _SYSTEM_PROMPT_BASE.format(retrieval_step=_PATH_B_RETRIEVAL)

# Assisted mode: invoice, PO and goods receipt come from deterministic extraction, so only the contract work is left.
_SYSTEM_PROMPT_ASSISTED = """You are an accounts-payable verification agent. Check one procurement package.
The invoice, purchase order and goods receipt have already been extracted and checked; the results are in the
first message. Do not read or submit them again. Missing documents are already recorded.

You have at most 10 turns.

Procedure:
1. If the invoice has no surcharges, call finish.
2. If it has surcharges: {retrieval_step}
   Then call check_surcharge for each surcharge with the clause's filename and page number.
   Set allowed=true only if the clause explicitly pre-approves this surcharge type.
3. Call finish.
Never output plain text. Every response must contain at least one tool call."""

SYSTEM_PROMPT_ASSISTED_A = _SYSTEM_PROMPT_ASSISTED.format(
    retrieval_step="use `search` with words about surcharges to find the surcharge clause in the master supply "
                   "agreement (MSA).")
SYSTEM_PROMPT_ASSISTED_B = _SYSTEM_PROMPT_ASSISTED.format(
    retrieval_step="use `read` to open 'msa/index.md', then read the section file it links for surcharges.")


# ------------------------------------------------------------------ tool argument schemas

def _parse_number(v: object) -> object:
    """The PDFs print German numbers ('1.525,20') and the model copies them verbatim on Path A.
    A comma marks the decimal point, so dots before it are thousands separators."""
    if isinstance(v, str):
        s = v.replace("€", "").replace(" ", "").strip()
        if "," in s:
            s = s.replace(".", "").replace(",", ".")
        return s
    return v


Num = Annotated[Decimal, BeforeValidator(_parse_number)]


def _numbers_in(text: str) -> set[Decimal]:
    """Every number printed in the text, read both the German way ('1.525,20', '2.400') and the English way
    ('1525.20', '1,000'), since retrieved PDFs and OKF files differ."""
    out: set[Decimal] = set()
    for tok in re.findall(r"\d[\d.,]*", text):
        tok = tok.rstrip(".,")
        candidates = {tok.replace(".", "").replace(",", "."), tok.replace(",", "")}
        for c in candidates:
            try:
                out.add(Decimal(c))
            except ArithmeticError:
                pass
    return out


def _printed_row(text: str, item_no: str) -> str:
    """The document's own row for an item, to quote back when a submitted value is not printed there.
    PDF text splits a table row over several lines, so a short line is extended with the lines after it."""
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if item_no in line:
            row = line if len(line) >= 30 or line.lstrip().startswith("|") else " ".join(lines[i:i + 9])
            return " ".join(row.split())[:160]
    return ""


class LineArg(BaseModel):
    item_no: str
    quantity: Num = Field(ge=0)
    unit_price: Num | None = None
    line_total: Num | None = None


class SurchargeArg(BaseModel):
    label: str
    amount: Num


class SubmitDocumentArgs(BaseModel):
    doc_type: Literal["invoice", "purchase_order", "goods_receipt"]
    document: str = Field(default="", description="Exact PDF filename from [source: filename.pdf] in retrieved text")
    lines: list[LineArg] = Field(min_length=1)
    surcharges: list[SurchargeArg] = []


class ReportMissingArgs(BaseModel):
    doc_type: Literal["invoice", "purchase_order", "goods_receipt"]


class CheckSurchargeArgs(BaseModel):
    label: str
    amount: Num | None = Field(default=None, description="the surcharge amount on the invoice")
    allowed: bool = Field(default=False, description="true only if the clause explicitly pre-approves this surcharge type without further approval")
    clause_document: str
    clause_page: int = Field(ge=1)
    reason: str = Field(default="", description="short explanation of why allowed is true or false")


class SearchArgs(BaseModel):
    query: str


class ReadArgs(BaseModel):
    paths: list[str] | str = Field(default_factory=list)
    path: list[str] | str | None = None  # models use either field, with one path or a list

    @model_validator(mode="before")
    @classmethod
    def _normalise(cls, data: object) -> object:
        """Qwen3-1.7b sometimes passes paths as a dict mapping labels to filenames.
        Flatten to a list of strings so validation succeeds."""
        if not isinstance(data, dict):
            return data
        for field in ("paths", "path"):
            v = data.get(field)
            if isinstance(v, dict):
                flat: list[str] = []
                for item in v.values():
                    if isinstance(item, str):
                        flat.append(item)
                    elif isinstance(item, list):
                        flat.extend(s for s in item if isinstance(s, str))
                data[field] = flat
        return data

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
ASSISTED_TOOLS = {"check_surcharge", "finish"}


# ------------------------------------------------------------------ retrieval adapters (the treatment)

class PathATools:
    name = "A"
    tools = [_tool("search", "Semantic search over all package documents. Returns the 5 most similar text chunks "
                   "with their document and page.", SearchArgs)]

    hint = ("Search with words from the text you need (e.g. the clause topic); "
            "a search for a filename or document number does not find the document.")

    def __init__(self, index: PathAIndex):
        self.index = index
        self.last_texts: dict[str, str] = {}  # document -> text revealed by the last call
        self._queries: set[str] = set()

    def resolve_document(self, name: str) -> str:
        return name

    def call(self, name: str, args: dict) -> tuple[str, set[tuple[str, int]]]:
        query = SearchArgs(**args).query
        chunks = self.index.search(query)
        text = "\n\n".join(f"[source: {c.document} page {c.page}]\n{c.text}" for c in chunks)
        if query.strip().lower() in self._queries:  # identical query -> identical results; say so instead of looping
            text = ("Note: you already searched for this; the results are the same. "
                    "Use different words if you need other text.\n\n" + text)
        self._queries.add(query.strip().lower())
        self.last_texts = {}
        for c in chunks:
            self.last_texts[c.document] = self.last_texts.get(c.document, "") + "\n" + c.text
        return text, {(c.document, c.page) for c in chunks}


class PathBTools:
    name = "B"
    tools = [_tool("read", "Open up to 5 files of the package knowledge bundle at once. Files: 'index.md' "
                   "(package overview), 'invoice.md', 'purchase_order.md', 'delivery_note.md', 'goods_receipt.md', "
                   "'guideline.md', 'msa/index.md' (list of contract sections) and the 'msa/...' section files linked "
                   "from it. Use full paths like 'msa/index.md'.", ReadArgs)]

    hint = "Open it with read; for the MSA read 'msa/index.md' first, then the section file it links."

    def __init__(self, bundle: PathBBundle):
        self.bundle = bundle
        self.last_texts: dict[str, str] = {}  # document -> text revealed by the last call

    def resolve_document(self, name: str) -> str:
        """Map OKF concept filenames (e.g. 'invoice.md') back to their source PDF."""
        if not name.endswith(".md"):
            return name
        concept_map = self.bundle._source_to_concept()
        for src, concept in concept_map.items():
            if concept == name:
                return src
        try:  # MSA section files etc.: their frontmatter names the source PDF
            return self.bundle.meta(name).get("source_document", name)
        except (FileNotFoundError, ValueError):
            return name

    def call(self, name: str, args: dict) -> tuple[str, set[tuple[str, int]]]:
        texts, seen = [], set()
        self.last_texts = {}
        for path in ReadArgs(**args).all_paths():
            try:
                text, meta = self.bundle.read(path), self.bundle.meta(path)
            except (FileNotFoundError, ValueError):
                texts.append(f"=== {path} ===\nError: no such file")
                continue
            pages = meta.get("pages") or ([meta["page"]] if "page" in meta else [1])
            if "source_document" in meta:
                seen |= {(meta["source_document"], int(pg)) for pg in pages}
            # Also track the concept file path so check_surcharge can cite it directly.
            seen |= {(path, int(pg)) for pg in pages}
            for doc in {path, meta.get("source_document", path)}:
                self.last_texts[doc] = self.last_texts.get(doc, "") + "\n" + text
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
    mode: str = "research"   # "assisted": invoice, PO and goods receipt pre-submitted from extraction
    compactions: int = 0     # retrieval results replaced by a one-line note to keep the context small
    extraction_check: dict | None = None  # self-check of the extraction (verified / uncertain + failed checks)
    notes: list[str] = field(default_factory=list)

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
        self.texts: dict[str, str] = {}  # document -> all text retrieval revealed from it
        self._turn_seen: set[str] | None = None  # documents seen before the current model response (None outside verify)
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
            raise ValueError(f"{where} has not been retrieved yet; retrieve it first and use its source filename. "
                             + self.retrieval.hint)

    # -------------------------------------------------- tools
    def _infer_document(self, doc_type: str) -> str:
        """When the model omits the filename, infer it from retrieved docs not yet submitted."""
        already = {v["document"] for v in self.run.submitted.values() if "document" in v}
        candidates = sorted({d for d, _ in self.seen} - already)
        if not candidates:
            retrieved = sorted({d for d, _ in self.seen}) or ["none yet"]
            raise ValueError(
                f"'document' field is required — include the PDF filename from [source: ...] in the retrieved text. "
                f"Retrieved so far: {', '.join(retrieved)}"
            )
        # Prefer a filename that hints at the doc_type; fall back to first candidate.
        hints = {"invoice": ("re-", "in", "invoice", "rechnung"),
                 "purchase_order": ("po-", "bes", "order"),
                 "goods_receipt": ("we-", "gr", "receipt", "wareneingang")}
        for c in candidates:
            if any(c.lower().startswith(h) or h in c.lower() for h in hints.get(doc_type, [])):
                return c
        return candidates[0]

    def _known_filenames(self) -> set[str]:
        return {d["file"] for d in self.documents}

    def _canonical(self, name: str) -> str:
        """Source filename for what the model wrote: OKF concept names map to their PDF, and a document number
        without extension ('MSA-LFT-PKV-2026-01') maps to the package file of that name."""
        name = self.retrieval.resolve_document(name.strip())
        known = self._known_filenames() | {d for d, _ in self.seen}
        if name in known:
            return name
        return next((k for k in known if k.lower() in (name.lower(), f"{name.lower()}.pdf")), name)

    def submit_document(self, a: SubmitDocumentArgs) -> str:
        if self.run.mode == "assisted":  # extraction already submitted and checked them; keep those values
            raise ValueError("The invoice, purchase order and goods receipt are already submitted from extraction. "
                             "Do not submit them again; continue with the surcharge check or call finish.")
        doc = a.document or self._infer_document(a.doc_type)
        doc = self._canonical(doc)
        known = self._known_filenames()
        if known and doc not in known:
            raise ValueError(f"{doc} is not in this package. Documents: {', '.join(sorted(known))}")
        self._require_seen(doc)  # a filename quoted inside another document (e.g. the PO number on the invoice) is not enough
        if self._turn_seen is not None and doc not in self._turn_seen:
            raise ValueError(f"{doc} was retrieved in this same response, so you have not seen its text yet. "
                             "Submit it in your next response, using the values shown in the retrieved text.")
        if a.doc_type == "goods_receipt":  # only the received quantity counts; drop prices the model may add
            a.lines = [ln.model_copy(update={"unit_price": None, "line_total": None}) for ln in a.lines]
        self._require_printed(doc, a)
        ref = SourceRef(document=doc, page=1)
        lines = [LineItem(item_no=ln.item_no, description="", quantity=ln.quantity, unit_price=ln.unit_price,
                          line_total=ln.line_total, source=ref) for ln in a.lines]
        if a.doc_type == "invoice":
            self.docs["invoice"] = Invoice(invoice_number=doc, po_number="", vendor="", lines=lines, source=ref,
                                           surcharges=[Surcharge(label=s.label, amount=s.amount, source=ref) for s in a.surcharges])
        elif a.doc_type == "purchase_order":
            self.docs["purchase_order"] = PurchaseOrder(po_number=doc, vendor="", lines=lines, source=ref)
        else:
            self.docs["goods_receipt"] = GoodsReceipt(receipt_number=doc, po_number="", lines=lines, source=ref)
        self.run.submitted[a.doc_type] = json.loads(a.model_dump_json()) | {"document": doc}
        return f"{a.doc_type} recorded with {len(lines)} line(s)."

    def _require_printed(self, doc: str, a: SubmitDocumentArgs):
        """Every submitted number must be printed in the retrieved text of that document."""
        text = self.texts.get(doc)
        if text is None:  # retrieval adapter without text tracking (tests)
            return
        printed = _numbers_in(text)
        wrong = [f"{ln.item_no} {field} {v}" for ln in a.lines
                 for field, v in (("quantity", ln.quantity), ("unit_price", ln.unit_price), ("line_total", ln.line_total))
                 if v is not None and v not in printed]
        wrong += [f"surcharge {s.label} {s.amount}" for s in a.surcharges if s.amount not in printed]
        if wrong:
            rows = [r for r in (_printed_row(text, w.split(" ")[0]) for w in wrong[:4]) if r]
            shown = f" {doc} shows: " + " / ".join(dict.fromkeys(rows)) + "." if rows else ""
            raise ValueError(f"These values are not in the retrieved text of {doc}: {'; '.join(wrong[:4])}.{shown} "
                             f"Submit the values printed in {doc} itself. If you have not seen its line items yet, "
                             f"retrieve them first. {self.retrieval.hint}")

    def _require_complete(self, inv, po, gr):
        """An invoice item printed in the retrieved PO / goods receipt must also be in that submission:
        checking only some lines hides the discrepancies on the others."""
        left_out = []
        for key, doc in (("purchase_order", po), ("goods_receipt", gr)):
            text = self.texts.get(self.run.submitted.get(key, {}).get("document", ""), "") if doc else ""
            have = {ln.item_no for ln in doc.lines} if doc else set()
            missing = [ln.item_no for ln in inv.lines if ln.item_no not in have and ln.item_no in text]
            if missing:
                left_out.append(f"{key}: {', '.join(missing)}")
        if left_out:
            raise ValueError("Submitted documents are incomplete; these invoice items are printed in them but were "
                             f"not submitted — {'; '.join(left_out)}. Resubmit with every line item, then run_checks.")

    def report_missing(self, a: ReportMissingArgs) -> str:
        if self.run.mode == "assisted":
            raise ValueError("Missing documents were already recorded from extraction. "
                             "Continue with the surcharge check or call finish.")
        self.missing.add(a.doc_type)
        return f"{a.doc_type} recorded as missing."

    def run_checks(self) -> str:
        inv, po, gr = (self.docs.get(k) for k in ("invoice", "purchase_order", "goods_receipt"))
        if inv is None:
            return "Error: submit the invoice first."
        self._require_complete(inv, po, gr)
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
        if po and (extra := unmatched_lines(po, inv)):
            lines.append("Invoice lines not on the purchase order: "
                         + ", ".join(f"{ln.item_no} ({ln.line_total})" for ln in extra)
                         + ". If such a line is an additional charge, resubmit the invoice with it under surcharges; "
                           "otherwise check that item_no is the article number printed on both documents.")
        if skipped:
            lines.append(f"Not checked because not submitted: {', '.join(skipped)}.")
        if inv.surcharges:
            lines.append("Invoice has surcharges: " + ", ".join(f"{s.label} {s.amount}" for s in inv.surcharges)
                         + ". Check them against the MSA.")
        return "\n".join(lines)

    def check_surcharge(self, a: CheckSurchargeArgs) -> str:
        inv = self.docs.get("invoice")
        if inv is None:
            raise ValueError("submit the invoice first")
        match = next((s for s in inv.surcharges if s.label.lower() == a.label.lower() or s.amount == a.amount), None)
        if match is None and len(inv.surcharges) == 1:  # one surcharge: a loose label still means that one
            match = inv.surcharges[0]
        if match is None:
            listed = ", ".join(f"{s.label} {s.amount}" for s in inv.surcharges)
            raise ValueError(f"The submitted invoice has surcharges: {listed}. Check one of those."
                             if listed else "The submitted invoice has no surcharges; nothing to check. Call finish.")
        a.label, a.amount = match.label, match.amount
        a.clause_document = self._canonical(a.clause_document)
        self._require_seen(a.clause_document)  # document-level: agent must have read the document, not a specific page
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
        unresolved = [doc_type for doc_type in ("invoice", "purchase_order", "goods_receipt")
                      if doc_type not in self.docs and doc_type not in self.missing]
        if unresolved:
            raise ValueError(f"Required documents unresolved: {', '.join(unresolved)}; submit them or report them missing")
        if not self.checks_ran and "invoice" not in self.missing:
            raise ValueError("run_checks has not completed; submit the documents and call run_checks first")
        checked = {c["label"] for c in self.run.cited_clauses}
        inv = self.docs.get("invoice")
        unchecked = [s.label for s in (inv.surcharges if inv else []) if s.label not in checked]
        if unchecked:
            raise ValueError(f"Surcharges not yet checked against the MSA: {', '.join(unchecked)}. "
                             "Retrieve the MSA surcharge clause and call check_surcharge first.")
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
                for doc, t in getattr(self.retrieval, "last_texts", {}).items():
                    self.texts[doc] = self.texts.get(doc, "") + t
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
            lines += [f"- {d['file']} ({d['type'].replace('_', ' ')}{', from the contract library' if d.get('library') else ''})"
                      for d in self.documents]
        if self.run.mode == "assisted":
            lines += ["", "The invoice, purchase order and goods receipt were already extracted, submitted and checked:",
                      self.precheck,
                      "Missing: " + (", ".join(sorted(self.missing)) if self.missing else "none") + ".",
                      self._assisted_task()]
        return "\n".join(lines)

    def _assisted_task(self) -> str:
        inv = self.docs.get("invoice")
        surcharges = inv.surcharges if inv else []
        if not surcharges:
            return "The invoice has no surcharges, so there is nothing left to check. Call finish."
        listed = "; ".join(f"{s.label} ({s.amount})" for s in surcharges)
        return (f"Remaining task: the invoice has surcharges: {listed}. Retrieve the MSA surcharge clause, call "
                "check_surcharge for each, then call finish.")

    def _consumed(self) -> set[str]:
        """Documents whose content the agent has already turned into submissions or citations."""
        return {v["document"] for v in self.run.submitted.values()} | {c["document"] for c in self.run.cited_clauses}

    def _compact(self, messages: list[dict], retrieved: list[dict], step: int):
        """Replace old or fully used retrieval results with a one-line note (same rule for both paths)."""
        consumed = self._consumed()
        for r in retrieved:
            if r["compacted"]:
                continue
            docs = {d for d, _ in r["seen"] if not d.endswith(".md")}  # exclude concept paths from compaction check
            if (docs and docs <= consumed) or step - r["step"] >= COMPACT_AFTER_STEPS:
                where = ", ".join(f"{d} p.{p}" for d, p in sorted(r["seen"])) or "nothing citable"
                messages[r["index"]]["content"] = (f"[Earlier {r['tool']} result for {r['args']} removed to keep the context "
                                                   f"small ({where}). Retrieve it again if you still need it.]")
                r["compacted"] = True
                self.run.compactions += 1

    def verify(self, client: ollama.Client | None = None, on_step: Callable[[Step], None] | None = None) -> AgentRun:
        client = client or ollama.Client()
        if self.run.mode == "assisted":  # documents are already submitted and checked: only the contract tools
            tools = self.retrieval.tools + [t for t in COMMON_TOOLS if t["function"]["name"] in ASSISTED_TOOLS]
            system_prompt = SYSTEM_PROMPT_ASSISTED_A if self.retrieval.name == "A" else SYSTEM_PROMPT_ASSISTED_B
        else:
            tools = self.retrieval.tools + COMMON_TOOLS
            system_prompt = SYSTEM_PROMPT_A if self.retrieval.name == "A" else SYSTEM_PROMPT_B
        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": self._task()}]
        retrieval_tools = {t["function"]["name"] for t in self.retrieval.tools}
        retrieved: list[dict] = []
        t_start = time.perf_counter()
        try:
            for step in range(1, MAX_STEPS + 1):
                t0 = time.perf_counter()
                self._turn_seen = {d for d, _ in self.seen}
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
