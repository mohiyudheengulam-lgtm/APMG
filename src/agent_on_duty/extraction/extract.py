"""Raw document extraction (Exposé §5.1). Each retrieval pipeline calls this itself with identical settings;
its run time counts towards that pipeline's preparation/build time.

Layout-independent: documents are classified by their most prominent title, and line-item tables
are read by word geometry (item-number column, column headers above it, numbers assigned to the
header they sit under). Numbers use German formatting (1.234,56).
"""

import json
import re
import shutil
import subprocess
import tempfile
import unicodedata
from decimal import Decimal, InvalidOperation
from enum import StrEnum
from pathlib import Path

import pymupdf
from pydantic import BaseModel

from agent_on_duty.schemas import GoodsReceipt, Invoice, LineItem, PurchaseOrder, SourceRef, Surcharge


class DocType(StrEnum):
    PURCHASE_ORDER = "purchase_order"
    DELIVERY_NOTE = "delivery_note"
    GOODS_RECEIPT = "goods_receipt"
    INVOICE = "invoice"
    MSA = "msa"
    GUIDELINE = "guideline"


class PageText(BaseModel):
    page: int
    text: str
    ocr: bool = False


class ExtractedDocument(BaseModel):
    filename: str
    doc_type: DocType
    title: str = ""
    pages: list[PageText]
    record: PurchaseOrder | GoodsReceipt | Invoice | None = None


class ExtractedPackage(BaseModel):
    package_id: str
    documents: list[ExtractedDocument]

    def get(self, doc_type: DocType) -> ExtractedDocument | None:
        return next((d for d in self.documents if d.doc_type == doc_type), None)


TITLE_PATTERNS = [  # most specific first; a title line naming several types resolves to the first match
    (re.compile(r"(master|framework)\s+(service|supply|purchase)?\s*agreement|supply\s+agreement", re.I), DocType.MSA),
    (re.compile(r"guideline|policy|richtlinie", re.I), DocType.GUIDELINE),
    (re.compile(r"goods\s+receipt|wareneingang", re.I), DocType.GOODS_RECEIPT),
    (re.compile(r"delivery\s+note|lieferschein", re.I), DocType.DELIVERY_NOTE),
    (re.compile(r"purchase\s+order|bestellung", re.I), DocType.PURCHASE_ORDER),
    (re.compile(r"\binvoice\b|rechnung", re.I), DocType.INVOICE),
]


# ------------------------------------------------------------------ text layer + OCR fallback

def norm(text: str) -> str:
    """Unicode NFKC: ligatures (ﬁ, ﬂ) and compatibility characters become plain text."""
    return unicodedata.normalize("NFKC", text)


def _words(page: pymupdf.Page) -> list[tuple]:
    return [(w[0], w[1], w[2], w[3], norm(w[4])) for w in page.get_text("words")]


def _ocr_page(page: pymupdf.Page) -> str:
    """Tesseract fallback at 300 DPI for pages without a text layer."""
    if not shutil.which("tesseract"):
        return ""
    with tempfile.TemporaryDirectory() as tmp:
        img = Path(tmp) / "page.png"
        page.get_pixmap(dpi=300).save(img)
        return subprocess.run(["tesseract", str(img), "-", "--psm", "6"], capture_output=True, text=True).stdout


def _page_texts(doc: pymupdf.Document) -> list[PageText]:
    out = []
    for page in doc:
        text = norm(page.get_text("text"))
        if text.strip():
            out.append(PageText(page=page.number + 1, text=text))
        else:
            out.append(PageText(page=page.number + 1, text=_ocr_page(page), ocr=True))
    return out


def classify(page: pymupdf.Page, text: str) -> tuple[DocType, str]:
    """The largest text on page 1 that names a document type decides (bodies mention other types too)."""
    spans = []
    for block in page.get_text("dict")["blocks"]:
        for line in block.get("lines", []):
            line_text = norm(" ".join(s["text"] for s in line["spans"])).strip()
            size = max((s["size"] for s in line["spans"]), default=0)
            if line_text:
                spans.append((size, line_text))
    by_size: dict[float, list[str]] = {}
    for size, line_text in spans:
        by_size.setdefault(round(size, 1), []).append(line_text)
    for size in sorted(by_size, reverse=True):
        if size < 9.5:
            break
        joined = " ".join(by_size[size])
        for pattern, doc_type in TITLE_PATTERNS:
            if pattern.search(joined):
                return doc_type, joined[:120]
    for pattern, doc_type in TITLE_PATTERNS:  # fallback: earliest mention in the text
        if pattern.search(text[:600]):
            return doc_type, ""
    raise ValueError("unrecognised document type")


# ------------------------------------------------------------------ numbers

NUM_RE = re.compile(r"^-?(\d{1,3}(\.\d{3})+|\d+)(,\d+)?$")


def parse_number(token: str) -> Decimal | None:
    """German format: 1.234,56 / 1.200 / 0,42 / -3."""
    token = token.strip().replace("−", "-")
    if not NUM_RE.match(token):
        return None
    try:
        return Decimal(token.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


# ------------------------------------------------------------------ table geometry

CODE_RE = re.compile(r"^[A-Z]{2,4}-[A-Za-z0-9][A-Za-z0-9.\-]*$")
DOCNUM_RE = re.compile(r"-20\d\d-|^MSA-|^PO-|^RE-|^LS-|^WE-|^DN-")


def _is_code(w: str) -> bool:
    return bool(CODE_RE.match(w)) and any(c.isdigit() for c in w) and not DOCNUM_RE.search(w)


def _column_role(label: str) -> str | None:
    words = set(re.findall(r"[a-z]+", label.lower()))
    if "price" in words:
        return "unit_price"
    if words & {"amount", "total", "value"}:
        return "line_total"
    if "received" in words:
        return "received"
    if words & {"shipped", "delivered", "dn"}:
        return "delivered"
    if "ordered" in words or ("po" in words and words & {"qty", "quantity"}):
        return "ordered"
    if words & {"backorder", "dev", "diff", "deviation"}:
        return None
    if words & {"qty", "quantity"}:
        return "qty"
    if words & {"description", "material", "item", "part"}:
        return "text"
    return None


def _columns(header_words: list[tuple]) -> list[dict]:
    """Merge header words into columns by horizontal overlap (multi-line labels stack vertically)."""
    cols: list[dict] = []
    for x0, y0, x1, y1, w in sorted(header_words, key=lambda t: t[0]):
        for c in cols:
            if x0 <= c["x1"] + 3.2 and x1 >= c["x0"] - 3.2 and (abs(y0 - c["y0"]) > 3 or x0 - c["x1"] < 3.2):
                c["x0"], c["x1"] = min(c["x0"], x0), max(c["x1"], x1)
                c["words"].append((y0, x0, w))
                break
        else:
            cols.append({"x0": x0, "x1": x1, "y0": y0, "words": [(y0, x0, w)]})
    for c in cols:
        c["label"] = " ".join(w for _, _, w in sorted(c["words"]))
        c["role"] = _column_role(c["label"])
    return cols


def _assign(x0: float, x1: float, cols: list[dict]) -> dict | None:
    best, best_overlap = None, 0.0
    for c in cols:
        overlap = min(x1, c["x1"]) - max(x0, c["x0"])
        if overlap > best_overlap:
            best, best_overlap = c, overlap
    if best:
        return best
    centre = (x0 + x1) / 2
    return min(cols, key=lambda c: min(abs(centre - c["x0"]), abs(centre - c["x1"])), default=None)


def _rows_of(words: list[tuple]) -> dict[int, list[tuple]]:
    rows: dict[int, list[tuple]] = {}
    for w in words:
        rows.setdefault(round((w[1] + w[3]) / 4), []).append(w)
    return {k: sorted(v) for k, v in rows.items()}


def _table_like(ws: list[tuple]) -> bool:
    """Header rows have wide gaps between cells; prose rows do not."""
    ws = sorted(ws)
    return len(ws) <= 3 or any(b[0] - a[2] > 15 for a, b in zip(ws, ws[1:]))


def _numeric_clusters(rows: list[list[tuple]]) -> list[dict]:
    """Columns of numbers that line up (right or left edge) in most item rows."""
    need = max(1, int(0.6 * len(rows) + 0.5))
    used: set[tuple] = set()
    clusters = []
    while True:
        counts: dict[tuple, list] = {}
        for i, row in enumerate(rows):
            for w in row:
                if w in used:
                    continue
                for key in (("r", round(w[2] / 5)), ("l", round(w[0] / 5))):
                    counts.setdefault(key, {}).setdefault(i, w)
        best = max(counts.items(), key=lambda kv: (len(kv[1]), kv[0][0] == "r"), default=None)
        if not best or len(best[1]) < need:
            return clusters
        members = best[1]
        used.update(members.values())
        clusters.append({"rows": members, "x0": min(w[0] for w in members.values()), "x1": max(w[2] for w in members.values())})


def parse_table(page: pymupdf.Page) -> tuple[list[dict], list[tuple[str, Decimal]]]:
    """Line items as {item_no, ordered, delivered, received, qty, unit_price, line_total}, plus surcharge rows."""
    words = _words(page)
    codes = [w for w in words if _is_code(w[4])]
    if not codes:
        return [], []
    groups: dict[int, list] = {}
    for w in codes:
        groups.setdefault(round(w[0] / 4), []).append(w)
    item_col = sorted(max(groups.values(), key=len), key=lambda w: w[1])
    first, last = item_col[0], item_col[-1]

    # header: lowest row above the items with >= 2 column labels, plus table-like rows just above it
    above = _rows_of([w for w in words if first[1] - 60 < w[3] <= first[1] + 0.5 and w[1] < first[1] - 1])
    labelled = [y for y, ws in above.items() if sum(_column_role(w[4]) is not None for w in ws) >= 2 and _table_like(ws)]
    if not labelled:
        return [], []
    low = max(labelled)
    header = [w for y, ws in above.items() if low - 7 <= y <= low and (y == low or _table_like(ws)) for w in ws]
    cols = [c for c in _columns(header) if c["role"] is not None]

    # numeric cells per item row (to the right of the item number, on the item's first line)
    item_rows = []
    for code in item_col:
        cells = [w for w in words if w[0] > code[2] and code[1] - 2 <= (w[1] + w[3]) / 2 <= code[3] + 2
                 and parse_number(w[4]) is not None]
        item_rows.append(cells)
    items = [{"item_no": c[4]} for c in item_col]
    # numeric columns are right-aligned under right-aligned labels: a header word belongs to the
    # first number column whose right edge reaches it (labels can be only a word-space apart)
    clusters = sorted(_numeric_clusters(item_rows), key=lambda c: c["x1"])
    for cl in clusters:
        cl["words"] = []
    for w in sorted(header, key=lambda w: (w[1], w[0])):
        if w[0] < first[2]:
            continue
        target = next((cl for cl in clusters if cl["x1"] >= w[2] - 2.5), None)
        if target:
            target["words"].append(w)
    numeric_cols = []
    for cl in clusters:
        role = _column_role(" ".join(w[4] for w in cl["words"]))
        col = {"role": role} if role not in (None, "text") else _assign(cl["x0"], cl["x1"], cols)
        if col is None or col["role"] in ("text", None):
            continue
        numeric_cols.append((cl, col))
        for i, w in cl["rows"].items():
            items[i].setdefault(col["role"], parse_number(w[4]))

    # additional-charge rows below the items: text label + value aligned with the amount column
    surcharges = []
    amount = next((cl for cl, col in numeric_cols if col["role"] == "line_total"), None)
    if amount:
        below = _rows_of([w for w in words if last[3] + 1 < w[1] < last[3] + 120])
        for _, ws in sorted(below.items()):
            texts = [w[4] for w in ws]
            if any(t.lower().rstrip(":") in {"net", "total", "subtotal", "vat", "amount", "plus"} for t in texts[:3]):
                break
            values = [w for w in ws if abs(w[2] - amount["x1"]) < 6 and parse_number(w[4]) is not None]
            label = " ".join(t for t in texts if parse_number(t) is None and t not in {"LS", "flat"})
            if values and re.search(r"surcharge|charge|fee|freight|handling|toll|energy|fuel", label, re.I):
                surcharges.append((label, parse_number(values[-1][4])))
    return items, surcharges


def _label_value(page: pymupdf.Page, labels: list[str]) -> str | None:
    """Value printed right after one of the labels on the same row."""
    text = norm(page.get_text("text"))
    lines = [ln.strip() for ln in text.splitlines()]
    for label in labels:
        pat = re.compile(rf"^{label}\s*:?\s*(\S+)?", re.I)
        for i, ln in enumerate(lines):
            m = pat.match(ln)
            if m:
                value = m.group(1) or (lines[i + 1] if i + 1 < len(lines) else None)
                if value and value.rstrip(":") and not value.endswith(":"):
                    return value
    return None


QTY_ROLE = {DocType.PURCHASE_ORDER: ("qty", "ordered"), DocType.DELIVERY_NOTE: ("delivered", "qty"),
            DocType.GOODS_RECEIPT: ("received", "qty"), DocType.INVOICE: ("qty", "ordered")}


def _lines(items: list[dict], doc_type: DocType, ref: SourceRef, priced: bool) -> list[LineItem]:
    out = []
    for it in items:
        qty = next((it[r] for r in QTY_ROLE[doc_type] if r in it), None)
        if qty is None:
            continue
        out.append(LineItem(item_no=it["item_no"], description="", quantity=qty,
                            unit_price=it.get("unit_price") if priced else None,
                            line_total=it.get("line_total") if priced else None, source=ref))
    return out


def extract_document(path: Path) -> ExtractedDocument:
    doc = pymupdf.open(path)
    pages = _page_texts(doc)
    doc_type, title = classify(doc[0], pages[0].text)
    ref = SourceRef(document=path.name, page=1)
    record = None
    if doc_type in QTY_ROLE:
        items, charges = parse_table(doc[0])
        p = doc[0]
        po_no = _label_value(p, ["Your order no\\.", "Customer PO", "PO number", "Purchase order no\\.", "PURCHASE ORDER",
                                 "Your order", "Purchase Order No\\."]) or ""
        if doc_type == DocType.PURCHASE_ORDER:
            record = PurchaseOrder(po_number=_label_value(p, ["PO number", "PO NUMBER", "Purchase Order No\\."]) or path.stem,
                                   vendor="", lines=_lines(items, doc_type, ref, True), source=ref)
        elif doc_type in (DocType.GOODS_RECEIPT, DocType.DELIVERY_NOTE):
            number = _label_value(p, ["GR document no\\.", "MATERIAL DOC\\.", "Delivery note no\\.", "Delivery note"]) or path.stem
            record = GoodsReceipt(receipt_number=number, po_number=po_no, lines=_lines(items, doc_type, ref, False), source=ref)
        else:
            vat = re.search(r"VAT\s*(\d{1,2})\s*%", pages[0].text)
            record = Invoice(invoice_number=_label_value(p, ["Invoice no\\.", "Invoice number"]) or path.stem,
                             po_number=po_no, vendor="", lines=_lines(items, doc_type, ref, True),
                             surcharges=[Surcharge(label=lbl, amount=amt, source=ref) for lbl, amt in charges],
                             tax_rate=Decimal(vat.group(1)) if vat else None, source=ref)
    return ExtractedDocument(filename=path.name, doc_type=doc_type, title=title, pages=pages, record=record)


def extract_package(package_dir: Path) -> ExtractedPackage:
    docs = [extract_document(p) for p in sorted(package_dir.glob("*.pdf"))]
    return ExtractedPackage(package_id=package_dir.name, documents=docs)


def save(pkg: ExtractedPackage, path: Path):
    path.write_text(pkg.model_dump_json(indent=1))


def load(path: Path) -> ExtractedPackage:
    return ExtractedPackage.model_validate(json.loads(path.read_text()))
