"""Self-check of an extraction against the documents' own control totals.

A package is "verified" when the extracted values reproduce what the documents print themselves:
invoice and PO lines (+ surcharges) add up to the printed net total, net + VAT = gross, every line has its
numbers, and goods receipt / delivery note list the PO's items with quantities. Otherwise it is "uncertain":
assisted mode then falls back to research mode and the manager sees a warning.

A wrong line on the document (quantity × price ≠ line total) is not an extraction failure: if the printed
lines still add up to the printed total, extraction read them correctly and the agent flags the discrepancy.
"""

import re
from decimal import Decimal
from pathlib import Path

import pymupdf
from pydantic import BaseModel

from agent_on_duty.extraction.extract import DocType, ExtractedDocument, ExtractedPackage, _rows_of, _words, detect_locale, parse_number

TOL = Decimal("0.01")
VAT_RE = re.compile(r"\b(vat|mwst|ust|umsatzsteuer|tax)\b", re.I)
NET_RE = re.compile(r"\b(net|netto|nettobetrag|subtotal|sub-total|zwischensumme|warenwert)\b", re.I)
GROSS_RE = re.compile(r"\b(gross|brutto|amount due|total due|invoice total|order total|total order value|"
                      r"rechnungsbetrag|gesamtbetrag|endbetrag)\b|^total\b", re.I)


class Check(BaseModel):
    document: str
    name: str
    ok: bool
    detail: str = ""


class ExtractionCheck(BaseModel):
    status: str  # "verified" | "uncertain"
    checks: list[Check]

    @property
    def problems(self) -> list[Check]:
        return [c for c in self.checks if not c.ok]


def printed_totals(path: Path) -> dict[str, Decimal]:
    """Net, VAT and gross amounts as printed on the document (first labelled row of each kind)."""
    doc = pymupdf.open(path)
    locale = detect_locale([w[4] for page in doc for w in _words(page)])
    out: dict[str, Decimal] = {}
    for page in doc:
        for _, ws in sorted(_rows_of(_words(page)).items()):
            text = " ".join(w[4] for w in ws)
            values = [v for v in (parse_number(w[4], locale) for w in ws) if v is not None]
            if not values:
                continue
            label = re.sub(r"[\d.,%€$]+", " ", text).strip()
            kind = "vat" if VAT_RE.search(label) else "net" if NET_RE.search(label) else "gross" if GROSS_RE.search(label) else None
            if kind and kind not in out:
                out[kind] = values[-1]
    return out


def _priced(doc: ExtractedDocument, path: Path) -> list[Check]:
    rec, name, checks = doc.record, doc.filename, []
    checks.append(Check(document=name, name="lines found", ok=bool(rec.lines), detail=f"{len(rec.lines)} line(s)"))
    incomplete = [ln.item_no for ln in rec.lines if None in (ln.quantity, ln.unit_price, ln.line_total)]
    checks.append(Check(document=name, name="every line has quantity, price and total", ok=not incomplete,
                        detail=", ".join(incomplete)))
    totals = printed_totals(path)
    lines_sum = sum((ln.line_total or Decimal(0) for ln in rec.lines), Decimal(0))
    charges = sum((s.amount for s in getattr(rec, "surcharges", [])), Decimal(0))
    if "net" in totals:
        diff = lines_sum + charges - totals["net"]
        checks.append(Check(document=name, name="lines + surcharges = printed net total", ok=abs(diff) <= TOL,
                            detail=f"{lines_sum + charges} vs {totals['net']}"))
    else:
        checks.append(Check(document=name, name="printed net total found", ok=False, detail="no net total on the document"))
    if {"net", "vat", "gross"} <= totals.keys():
        checks.append(Check(document=name, name="net + VAT = printed gross", ok=abs(totals["net"] + totals["vat"] - totals["gross"]) <= TOL,
                            detail=f"{totals['net']} + {totals['vat']} vs {totals['gross']}"))
    return checks


def _quantities(doc: ExtractedDocument, po_items: set[str] | None) -> list[Check]:
    rec, name = doc.record, doc.filename
    checks = [Check(document=name, name="lines found", ok=bool(rec.lines), detail=f"{len(rec.lines)} line(s)")]
    if po_items is not None:
        items = {ln.item_no for ln in rec.lines}
        checks.append(Check(document=name, name="same items as the purchase order", ok=items == po_items,
                            detail=f"missing {sorted(po_items - items)}, extra {sorted(items - po_items)}" if items != po_items else ""))
    return checks


def check_package(pkg: ExtractedPackage, package_dir: Path) -> ExtractionCheck:
    checks: list[Check] = []
    po = pkg.get(DocType.PURCHASE_ORDER)
    po_ok = False
    for dt in (DocType.INVOICE, DocType.PURCHASE_ORDER):
        d = pkg.get(dt)
        if d and d.record:
            doc_checks = _priced(d, package_dir / d.filename)
            checks += doc_checks
            po_ok = po_ok or (dt == DocType.PURCHASE_ORDER and all(c.ok for c in doc_checks))
    po_items = {ln.item_no for ln in po.record.lines} if po and po.record and po_ok else None
    for dt in (DocType.GOODS_RECEIPT, DocType.DELIVERY_NOTE):
        d = pkg.get(dt)
        if d and d.record:
            checks += _quantities(d, po_items)
    if not pkg.get(DocType.INVOICE):
        checks.append(Check(document="-", name="invoice found", ok=False, detail="no invoice recognised in the package"))
    return ExtractionCheck(status="verified" if all(c.ok for c in checks) else "uncertain", checks=checks)


def check_document(doc: ExtractedDocument, path: Path) -> ExtractionCheck:
    """Single invoice / PO (used for layout tests)."""
    checks = _priced(doc, path)
    return ExtractionCheck(status="verified" if all(c.ok for c in checks) else "uncertain", checks=checks)
