"""Raw document extraction (Exposé §5.1). Each retrieval pipeline calls this itself with identical settings;
its run time counts towards that pipeline's preparation/build time."""

import json
import re
import shutil
import subprocess
import tempfile
from decimal import Decimal
from enum import StrEnum
from pathlib import Path

import pymupdf
from pydantic import BaseModel

from agent_on_duty.schemas import GoodsReceipt, Invoice, LineItem, PurchaseOrder, SourceRef, Surcharge


class DocType(StrEnum):
    PURCHASE_ORDER = "purchase_order"
    GOODS_RECEIPT = "goods_receipt"
    INVOICE = "invoice"
    MSA = "msa"


class PageText(BaseModel):
    page: int
    text: str
    ocr: bool = False


class ExtractedDocument(BaseModel):
    filename: str
    doc_type: DocType
    pages: list[PageText]
    record: PurchaseOrder | GoodsReceipt | Invoice | None = None


class ExtractedPackage(BaseModel):
    package_id: str
    documents: list[ExtractedDocument]

    def get(self, doc_type: DocType) -> ExtractedDocument | None:
        return next((d for d in self.documents if d.doc_type == doc_type), None)


TITLES = {
    "PURCHASE ORDER": DocType.PURCHASE_ORDER,
    "GOODS RECEIPT": DocType.GOODS_RECEIPT,
    "DELIVERY NOTE": DocType.GOODS_RECEIPT,
    "INVOICE": DocType.INVOICE,
    "MASTER SERVICE AGREEMENT": DocType.MSA,
}


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
        text = page.get_text("text")
        if text.strip():
            out.append(PageText(page=page.number + 1, text=text))
        else:
            out.append(PageText(page=page.number + 1, text=_ocr_page(page), ocr=True))
    return out


def classify(pages: list[PageText]) -> DocType:
    """Earliest title on the first page wins (an MSA body mentions 'purchase order' too)."""
    head = pages[0].text.upper()[:400]
    hits = [(head.find(title), doc_type) for title, doc_type in TITLES.items() if title in head]
    if not hits:
        raise ValueError("unrecognised document type")
    return min(hits)[1]


def _money(s: str) -> Decimal:
    return Decimal(s.replace(",", ""))


def _rows(page: pymupdf.Page) -> list[list[tuple[float, str]]]:
    """Group words into visual rows by baseline, each row a list of (x0, word)."""
    rows: dict[int, list[tuple[float, str]]] = {}
    for x0, _y0, _x1, y1, word, *_ in page.get_text("words"):
        rows.setdefault(round(y1), []).append((x0, word))
    return [sorted(r) for _, r in sorted(rows.items())]


def _header_fields(page: pymupdf.Page) -> dict[str, str]:
    """'Key: Value' rows from the header block, read by visual row."""
    fields = {}
    for row in _rows(page):
        words = [w for _, w in row]
        for i, w in enumerate(words):
            if w.endswith(":"):
                fields[" ".join(words[: i + 1])[:-1].lower()] = " ".join(words[i + 1:])
                break
    return fields


ITEM_RE = re.compile(r"^[A-Z]-\d{2,3}$")
NUM_RE = re.compile(r"^[\d,]+(\.\d{2})?$")


def _table(page: pymupdf.Page, ref: SourceRef, priced: bool) -> tuple[list[LineItem], list[Surcharge]]:
    """Line items start with an item code; trailing numeric tokens are qty [, unit price, line total]."""
    items, surcharges = [], []
    in_charges = False
    for row in _rows(page):
        words = [w for _, w in row]
        if words[:2] == ["Additional", "Charges"]:
            in_charges = True
            continue
        if ITEM_RE.match(words[0]):
            n_num = 3 if priced else 1
            nums, desc = words[-n_num:], words[1:-n_num]
            if not all(NUM_RE.match(n) for n in nums):
                continue
            items.append(LineItem(
                item_no=words[0], description=" ".join(desc), quantity=_money(nums[0]),
                unit_price=_money(nums[1]) if priced else None,
                line_total=_money(nums[2]) if priced else None, source=ref,
            ))
        elif in_charges and words[0] != "Total" and NUM_RE.match(words[-1]):
            surcharges.append(Surcharge(label=" ".join(words[:-1]), amount=_money(words[-1]), source=ref))
        elif words[0] == "Total":
            in_charges = False
    return items, surcharges


def extract_document(path: Path) -> ExtractedDocument:
    doc = pymupdf.open(path)
    pages = _page_texts(doc)
    doc_type = classify(pages)
    ref = SourceRef(document=path.name, page=1)
    f = _header_fields(doc[0])
    record = None
    if doc_type == DocType.PURCHASE_ORDER:
        lines, _ = _table(doc[0], ref, priced=True)
        record = PurchaseOrder(po_number=f["po number"], vendor=f["vendor"], currency=f.get("currency", "EUR"),
                               lines=lines, source=ref)
    elif doc_type == DocType.GOODS_RECEIPT:
        lines, _ = _table(doc[0], ref, priced=False)
        record = GoodsReceipt(receipt_number=f["receipt number"], po_number=f["po number"], lines=lines, source=ref)
    elif doc_type == DocType.INVOICE:
        lines, charges = _table(doc[0], ref, priced=True)
        record = Invoice(invoice_number=f["invoice number"], po_number=f["po number"], vendor=f["vendor"],
                         currency=f.get("currency", "EUR"), lines=lines, surcharges=charges,
                         tax_rate=_money(f["vat rate"].rstrip("%")) if "vat rate" in f else None, source=ref)
    return ExtractedDocument(filename=path.name, doc_type=doc_type, pages=pages, record=record)


def extract_package(package_dir: Path) -> ExtractedPackage:
    docs = [extract_document(p) for p in sorted(package_dir.glob("*.pdf"))]
    return ExtractedPackage(package_id=package_dir.name, documents=docs)


def save(pkg: ExtractedPackage, path: Path):
    path.write_text(pkg.model_dump_json(indent=1))


def load(path: Path) -> ExtractedPackage:
    return ExtractedPackage.model_validate(json.loads(path.read_text()))
