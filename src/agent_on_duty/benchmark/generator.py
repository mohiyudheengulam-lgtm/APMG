"""Programmatic benchmark generation (Exposé §6.2, §7.1).

Each package is a folder with digital PDFs (PO, goods receipt, invoice, MSA) plus ground_truth.json.
The generator, not the agent, defines the ground truth.
"""

import json
import random
import shutil
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

import pymupdf

from agent_on_duty.benchmark.seeds import FILLER, SEEDS

Q = Decimal("0.01")
VAT_RATE = Decimal(19)

# (case_type, vendor) in generation order — 24 packages
CASE_PLAN = [
    ("compliant", "ACME"), ("compliant", "NORD"), ("compliant", "ACME"), ("compliant", "NORD"), ("compliant", "ACME"),
    ("quantity", "ACME"), ("quantity", "NORD"), ("quantity", "ACME"), ("quantity", "NORD"),
    ("price", "ACME"), ("price", "NORD"), ("price", "ACME"), ("price", "NORD"),
    ("line_total", "ACME"), ("line_total", "NORD"), ("line_total", "ACME"),
    ("surcharge_violation", "ACME"), ("surcharge_violation", "NORD"), ("surcharge_violation", "NORD"),
    ("surcharge_allowed", "NORD"), ("surcharge_allowed", "NORD"),
    ("missing_receipt", "ACME"), ("missing_po", "NORD"),
    ("combined", "ACME"),  # the Exposé §1 example shape: quantity + price + surcharge
]


@dataclass
class Line:
    item_no: str
    description: str
    po_qty: int
    po_price: Decimal
    gr_qty: int
    inv_qty: int
    inv_price: Decimal
    inv_total: Decimal | None = None  # None → computed correctly

    @property
    def invoiced_total(self) -> Decimal:
        return self.inv_total if self.inv_total is not None else (self.inv_qty * self.inv_price).quantize(Q)


@dataclass
class Package:
    package_id: str
    case_type: str
    vendor: dict
    rate_card: dict[str, Decimal]
    lines: list[Line]
    surcharges: list[tuple[str, Decimal]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    po_number: str = ""
    gr_number: str = ""
    inv_number: str = ""
    issue_date: date = date(2026, 9, 1)


def _rate_cards(rng: random.Random) -> dict[str, dict[str, Decimal]]:
    return {
        code: {item: (Decimal(rng.randrange(250, 9500)) / 100).quantize(Q) for item, _ in seed["catalogue"]}
        for code, seed in SEEDS.items()
    }


def build_package(idx: int, case_type: str, vendor_code: str, rng: random.Random, rates) -> Package:
    vendor = SEEDS[vendor_code]
    rate_card = rates[vendor_code]
    n_lines = 1 if case_type == "combined" else rng.randint(1, 3)
    items = rng.sample(vendor["catalogue"], n_lines)
    lines = []
    for item_no, desc in items:
        qty = rng.choice([50, 80, 100, 120, 150, 200, 240, 300, 400, 480, 500, 600, 750])
        price = rate_card[item_no]
        lines.append(Line(item_no, desc, qty, price, qty, qty, price))

    pkg = Package(
        package_id=f"PKG-{idx:03d}",
        case_type=case_type,
        vendor=vendor,
        rate_card=rate_card,
        lines=lines,
        po_number=f"PO-2026-{4100 + idx}",
        gr_number=f"GR-2026-{7300 + idx}",
        inv_number=f"{vendor_code}-INV-{88000 + idx * 7}",
        issue_date=date(2026, 9, 1) + timedelta(days=idx),
    )
    target = rng.choice(lines)

    if case_type == "quantity":
        short = rng.choice([5, 10, 20, 25])
        target.gr_qty = target.po_qty - short
    elif case_type == "price":
        target.inv_price = (target.po_price * Decimal(rng.choice(["1.03", "1.05", "1.08"]))).quantize(Q)
    elif case_type == "line_total":
        target.inv_total = (target.inv_qty * target.inv_price).quantize(Q) + Decimal(rng.choice([10, 45, 90, 100]))
    elif case_type == "surcharge_violation":
        if vendor_code == "ACME":
            pkg.surcharges = [(rng.choice(["Fuel surcharge", "Handling fee", "Energy surcharge"]), Decimal(rng.choice([75, 120, 150])))]
        else:
            pkg.surcharges = rng.choice([
                [("Freight surcharge", Decimal(rng.choice([140, 180, 225])))],
                [("Energy surcharge", Decimal(rng.choice([60, 95])))],
            ])
    elif case_type == "surcharge_allowed":
        pkg.surcharges = [("Freight surcharge", Decimal(rng.choice([45, 80, 100])))]
    elif case_type == "missing_receipt":
        pkg.missing = ["goods_receipt"]
    elif case_type == "missing_po":
        pkg.missing = ["purchase_order"]
    elif case_type == "combined":
        target.po_qty = target.inv_qty = 500
        target.gr_qty = 480
        target.inv_price = (target.po_price * Decimal("1.0333")).quantize(Q)
        pkg.surcharges = [("Fuel surcharge", Decimal(150))]
    return pkg


# ---------------------------------------------------------------- ground truth

def _surcharge_clause(vendor: dict) -> tuple[str, int, str]:
    for page, (clause_id, topic, _title, body) in enumerate(vendor["sections"], start=1):
        if topic == "surcharges":
            return clause_id, page, body
    raise ValueError("seed has no surcharge section")


def _pricing_page(vendor: dict) -> int:
    return next(p for p, s in enumerate(vendor["sections"], start=1) if s[1] == "pricing")


def surcharge_allowed(vendor: dict, label: str, amount: Decimal) -> bool:
    if vendor["surcharge_policy"] == "prohibited":
        return False
    return label.lower().startswith("freight") and amount <= vendor["freight_cap"]


def ground_truth(pkg: Package) -> dict:
    files = doc_files(pkg)
    msa_file = files["msa"]
    has_po = "purchase_order" not in pkg.missing
    has_gr = "goods_receipt" not in pkg.missing

    def line_fields(kind):
        out = []
        for ln in pkg.lines:
            if kind == "purchase_order":
                out.append({"item_no": ln.item_no, "quantity": str(ln.po_qty), "unit_price": str(ln.po_price),
                            "line_total": str((ln.po_qty * ln.po_price).quantize(Q))})
            elif kind == "goods_receipt":
                out.append({"item_no": ln.item_no, "quantity": str(ln.gr_qty)})
            else:
                out.append({"item_no": ln.item_no, "quantity": str(ln.inv_qty), "unit_price": str(ln.inv_price),
                            "line_total": str(ln.invoiced_total)})
        return out

    fields = {"invoice": {"invoice_number": pkg.inv_number, "po_number": pkg.po_number, "lines": line_fields("invoice"),
                          "surcharges": [{"label": lbl, "amount": str(a.quantize(Q))} for lbl, a in pkg.surcharges],
                          "tax_rate": str(VAT_RATE)}}
    if has_po:
        fields["purchase_order"] = {"po_number": pkg.po_number, "lines": line_fields("purchase_order")}
    if has_gr:
        fields["goods_receipt"] = {"receipt_number": pkg.gr_number, "po_number": pkg.po_number,
                                   "lines": line_fields("goods_receipt")}

    findings = []
    for doc in pkg.missing:
        findings.append({"flag": "FLAGGED_MISSING_DOCUMENT", "document_type": doc})
    for ln in pkg.lines:
        if has_gr and ln.inv_qty != ln.gr_qty:
            findings.append({
                "flag": "FLAGGED_QUANTITY_MISMATCH", "error_type": "quantity", "item_no": ln.item_no,
                "expected": str(ln.gr_qty), "actual": str(ln.inv_qty),
                "amount": str(((ln.inv_qty - ln.gr_qty) * ln.po_price).quantize(Q)),
                "evidence": [{"document": files["invoice"], "page": 1}, {"document": files["goods_receipt"], "page": 1}],
            })
        if has_po and ln.inv_price != ln.po_price:
            findings.append({
                "flag": "FLAGGED_PRICE_MISMATCH", "error_type": "price", "item_no": ln.item_no,
                "expected": str(ln.po_price), "actual": str(ln.inv_price),
                "amount": str(((ln.inv_price - ln.po_price) * ln.inv_qty).quantize(Q)),
                "evidence": [{"document": files["invoice"], "page": 1}, {"document": files["purchase_order"], "page": 1}],
            })
        if ln.inv_total is not None:
            expected = (ln.inv_qty * ln.inv_price).quantize(Q)
            findings.append({
                "flag": "FLAGGED_LINE_TOTAL_MISMATCH", "error_type": "line_total", "item_no": ln.item_no,
                "expected": str(expected), "actual": str(ln.inv_total), "amount": str(ln.inv_total - expected),
                "evidence": [{"document": files["invoice"], "page": 1}],
            })

    clause_id, clause_page, clause_text = _surcharge_clause(pkg.vendor)
    for label, amount in pkg.surcharges:
        if not surcharge_allowed(pkg.vendor, label, amount):
            findings.append({
                "flag": "FLAGGED_SURCHARGE", "error_type": "surcharge", "label": label, "amount": str(amount.quantize(Q)),
                "evidence": [{"document": files["invoice"], "page": 1}, {"document": msa_file, "page": clause_page}],
            })

    flags = sorted({f["flag"] for f in findings})
    return {
        "package_id": pkg.package_id,
        "case_type": pkg.case_type,
        "vendor": pkg.vendor["code"],
        "documents": {k: v for k, v in files.items() if k not in pkg.missing},
        "missing_documents": pkg.missing,
        "fields": fields,
        "expected_findings": findings,
        "expected_flags": flags,
        "expected_recommendation": ",".join(flags) if flags else "NO_DISCREPANCY",
        "msa_clauses": {
            "surcharges": {"clause_id": clause_id, "document": msa_file, "page": clause_page, "text": clause_text},
            "pricing": {"document": msa_file, "page": _pricing_page(pkg.vendor)},
        },
        "surcharge_relevant": bool(pkg.surcharges),
    }


# ---------------------------------------------------------------- PDF rendering

def doc_files(pkg: Package) -> dict[str, str]:
    return {
        "purchase_order": f"{pkg.po_number}.pdf",
        "goods_receipt": f"{pkg.gr_number}.pdf",
        "invoice": f"{pkg.inv_number}.pdf",
        "msa": f"MSA-{pkg.vendor['code']}.pdf",
    }


FONT, BOLD = "helv", "hebo"
COLS = {"item": 50, "desc": 110, "qty": 360, "price": 420, "total": 500}


def _money(v: Decimal) -> str:
    return f"{v:,.2f}"


def _header(page, title: str, rows: list[tuple[str, str]], vendor: dict) -> float:
    page.insert_text((50, 60), title, fontname=BOLD, fontsize=18)
    y = 90
    for k, v in rows:
        page.insert_text((50, y), f"{k}:", fontname=BOLD, fontsize=10)
        page.insert_text((170, y), v, fontname=FONT, fontsize=10)
        y += 15
    return y + 15


def _table_header(page, y: float, with_prices: bool, qty_label: str) -> float:
    page.insert_text((COLS["item"], y), "Item", fontname=BOLD, fontsize=10)
    page.insert_text((COLS["desc"], y), "Description", fontname=BOLD, fontsize=10)
    page.insert_text((COLS["qty"], y), qty_label, fontname=BOLD, fontsize=10)
    if with_prices:
        page.insert_text((COLS["price"], y), "Unit Price", fontname=BOLD, fontsize=10)
        page.insert_text((COLS["total"], y), "Line Total", fontname=BOLD, fontsize=10)
    page.draw_line((45, y + 5), (560, y + 5))
    return y + 20


def _row(page, y, item, desc, qty, price=None, total=None):
    page.insert_text((COLS["item"], y), item, fontname=FONT, fontsize=10)
    page.insert_text((COLS["desc"], y), desc[:42], fontname=FONT, fontsize=10)
    page.insert_text((COLS["qty"], y), str(qty), fontname=FONT, fontsize=10)
    if price is not None:
        page.insert_text((COLS["price"], y), _money(price), fontname=FONT, fontsize=10)
        page.insert_text((COLS["total"], y), _money(total), fontname=FONT, fontsize=10)
    return y + 16


def render_po(pkg: Package, path: Path):
    doc = pymupdf.open()
    page = doc.new_page()
    y = _header(page, "PURCHASE ORDER", [
        ("PO Number", pkg.po_number), ("Date", pkg.issue_date.isoformat()),
        ("Buyer", pkg.vendor["buyer"]), ("Vendor", pkg.vendor["name"]), ("Currency", "EUR"),
        ("Contract", f"MSA-{pkg.vendor['code']}"),
    ], pkg.vendor)
    y = _table_header(page, y, True, "Qty")
    total = Decimal(0)
    for ln in pkg.lines:
        lt = (ln.po_qty * ln.po_price).quantize(Q)
        total += lt
        y = _row(page, y, ln.item_no, ln.description, ln.po_qty, ln.po_price, lt)
    page.insert_text((COLS["price"], y + 10), "Total", fontname=BOLD, fontsize=10)
    page.insert_text((COLS["total"], y + 10), _money(total), fontname=BOLD, fontsize=10)
    doc.save(path)


def render_gr(pkg: Package, path: Path):
    doc = pymupdf.open()
    page = doc.new_page()
    y = _header(page, "GOODS RECEIPT / DELIVERY NOTE", [
        ("Receipt Number", pkg.gr_number), ("PO Number", pkg.po_number),
        ("Received On", (pkg.issue_date + timedelta(days=6)).isoformat()),
        ("Vendor", pkg.vendor["name"]), ("Warehouse", "Main Warehouse, Gate 3"),
    ], pkg.vendor)
    y = _table_header(page, y, False, "Qty Received")
    for ln in pkg.lines:
        y = _row(page, y, ln.item_no, ln.description, ln.gr_qty)
    page.insert_text((50, y + 20), "Received and inspected by: Warehouse Team B", fontname=FONT, fontsize=9)
    doc.save(path)


def render_invoice(pkg: Package, path: Path):
    doc = pymupdf.open()
    page = doc.new_page()
    y = _header(page, "INVOICE", [
        ("Invoice Number", pkg.inv_number), ("PO Number", pkg.po_number),
        ("Invoice Date", (pkg.issue_date + timedelta(days=8)).isoformat()),
        ("Vendor", pkg.vendor["name"]), ("Bill To", pkg.vendor["buyer"]), ("Currency", "EUR"),
        ("VAT Rate", f"{VAT_RATE}%"),
    ], pkg.vendor)
    y = _table_header(page, y, True, "Qty")
    subtotal = Decimal(0)
    for ln in pkg.lines:
        subtotal += ln.invoiced_total
        y = _row(page, y, ln.item_no, ln.description, ln.inv_qty, ln.inv_price, ln.invoiced_total)
    y += 10
    if pkg.surcharges:
        page.insert_text((50, y), "Additional Charges", fontname=BOLD, fontsize=10)
        y += 16
        for label, amount in pkg.surcharges:
            page.insert_text((COLS["desc"], y), label, fontname=FONT, fontsize=10)
            page.insert_text((COLS["total"], y), _money(amount), fontname=FONT, fontsize=10)
            y += 16
    total = subtotal + sum((a for _, a in pkg.surcharges), Decimal(0))
    page.insert_text((COLS["price"], y + 10), "Total", fontname=BOLD, fontsize=10)
    page.insert_text((COLS["total"], y + 10), _money(total), fontname=BOLD, fontsize=10)
    vat = (total * VAT_RATE / 100).quantize(Q)
    page.insert_text((COLS["price"], y + 26), f"VAT {VAT_RATE}%", fontname=FONT, fontsize=10)
    page.insert_text((COLS["total"], y + 26), _money(vat), fontname=FONT, fontsize=10)
    page.insert_text((COLS["price"], y + 42), "Amount Due", fontname=BOLD, fontsize=10)
    page.insert_text((COLS["total"], y + 42), _money(total + vat), fontname=BOLD, fontsize=10)
    doc.save(path)


def render_msa(pkg: Package, path: Path):
    vendor = pkg.vendor
    doc = pymupdf.open()
    for clause_id, topic, title, body in vendor["sections"]:
        page = doc.new_page()
        text = f"Section {clause_id}. {title}\n\n{clause_id}.1 {body}\n\n{clause_id}.2 {FILLER}\n\n{clause_id}.3 {FILLER}"
        if topic == "pricing":
            text = f"Section {clause_id}. {title}\n\n{clause_id}.1 {body}\n\nRate Card (EUR per unit):\n"
            text += "\n".join(f"{item}  {desc}  {_money(vendor_rate)}"
                              for (item, desc), vendor_rate in ((c, pkg.rate_card[c[0]]) for c in vendor["catalogue"]))
        header = f"Master Service Agreement between {vendor['buyer']} and {vendor['name']}"
        page.insert_text((50, 40), header, fontname=FONT, fontsize=8)
        page.insert_textbox(pymupdf.Rect(50, 60, 545, 780), text, fontname=FONT, fontsize=10)
        page.insert_text((280, 810), f"Page {page.number + 1}", fontname=FONT, fontsize=8)
    doc.save(path)


def write_package(pkg: Package, out_dir: Path) -> dict:
    pdir = out_dir / pkg.package_id
    if pdir.exists():
        shutil.rmtree(pdir)
    pdir.mkdir(parents=True)
    files = doc_files(pkg)
    if "purchase_order" not in pkg.missing:
        render_po(pkg, pdir / files["purchase_order"])
    if "goods_receipt" not in pkg.missing:
        render_gr(pkg, pdir / files["goods_receipt"])
    render_invoice(pkg, pdir / files["invoice"])
    render_msa(pkg, pdir / files["msa"])
    gt = ground_truth(pkg)
    (pdir / "ground_truth.json").write_text(json.dumps(gt, indent=2))
    return gt


def generate(out_dir: Path, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    rates = _rate_cards(rng)
    out_dir.mkdir(parents=True, exist_ok=True)
    return [write_package(build_package(i, case, vendor, rng, rates), out_dir)
            for i, (case, vendor) in enumerate(CASE_PLAN, start=1)]
