"""Benchmark generation from the realistic seed packages (Exposé §7.1).

Each seed (one buyer–supplier relationship, its MSA and purchasing guideline) is expanded into
12 packages: new order lines from the MSA price list, new document numbers and dates, and one
injected case per package. Transactional PDFs (PO, delivery note, goods receipt, invoice) are rendered
with the seed's own layouts. The seed's MSA and purchasing guideline go into the contract library once
(data/contracts) and are linked to packages by the MSA number / buyer name on the invoice and PO.

    uv run python scripts/dataset_generator.py        # writes data/packages/PKG-NNN/
"""

from __future__ import annotations

import copy
import json
import random
import re
import shutil
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import package_1  # noqa: E402
import package_2  # noqa: E402
from common import SEEDS_OUT, D, compute_master, doc_view, q2, render_pdf, s2  # noqa: E402

SEEDS = [package_1, package_2]
TRANSACTIONAL = ("purchase_order", "delivery_note", "goods_receipt", "invoice")

# per seed, in order; 12 packages each
CASES = {
    "seed_01_packaging_fasteners": [
        "compliant", "quantity", "price", "surcharge", "compliant", "line_total",
        "quantity_partial", "price", "missing_receipt", "surcharge", "combined", "compliant",
    ],
    "seed_02_electronic_components": [
        "compliant", "price", "quantity", "surcharge", "line_total", "compliant",
        "missing_po", "quantity_partial", "surcharge", "price", "combined", "compliant",
    ],
}
SURCHARGES = {
    "seed_01_packaging_fasteners": ["Fuel surcharge (diesel price adjustment)", "Energy surcharge", "Pallet handling fee"],
    "seed_02_electronic_components": ["Freight surcharge express", "Small-quantity surcharge", "Energy cost surcharge"],
}


def _shift(iso: str, days: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=days)).isoformat()


def _bump(number: str, k: int) -> str:
    """Change the last digit group of a document number, keeping its format."""
    m = list(re.finditer(r"\d+", number))[-1]
    width = len(m.group())
    return number[: m.start()] + str(int(m.group()) + k * 7 + 3).zfill(width) + number[m.end():]


def filename(number: str) -> str:
    return re.sub(r"[^A-Za-z0-9._-]+", "-", number).strip("-") + ".pdf"


def make_config(seed, k: int, rng: random.Random) -> dict:
    cfg = copy.deepcopy(seed.CONFIG)
    price_list = cfg["price_list"]
    n = rng.randint(6, min(8, len(price_list)))
    picks = sorted(rng.sample(range(len(price_list)), n))
    base_qty = {li["item_no"]: li["quantity"] for li in seed.CONFIG["order_items"]}
    items = []
    for i in picks:
        p = price_list[i]
        q0 = base_qty.get(p["item_no"]) or rng.choice([10, 20, 50, 100, 200, 500])
        qty = max(1, int(q0 * rng.choice([0.5, 0.8, 1, 1, 1.25, 1.5, 2])))
        if q0 >= 100:
            qty = round(qty, -1)
        items.append({k2: p[k2] for k2 in ("item_no", "description", "unit", "unit_price")} | {"quantity": qty})
    cfg["order_items"] = items
    days = 9 * k + rng.randint(0, 5)
    d = cfg["documents"]
    for key in ("purchase_order", "delivery_note", "goods_receipt", "invoice"):
        d[key]["number"] = _bump(d[key]["number"], k)
    for key, fields in {"purchase_order": ("date", "requested_delivery_date"), "delivery_note": ("date",),
                        "goods_receipt": ("date",), "invoice": ("date", "due_date", "discount_deadline")}.items():
        for f in fields:
            d[key][f] = _shift(d[key][f], days)
    return cfg


def inject(case: str, m: dict, seed_name: str, rng: random.Random) -> tuple[dict, list[str]]:
    """Return (variant overrides, missing documents)."""
    lines = m["line_items"]
    v: dict = {}
    missing: list[str] = []

    def short_qty(li):
        q = li["quantity"]
        return max(1, q - max(1, round(q * rng.choice([0.05, 0.1, 0.2]))))

    def pick():
        return rng.choice(lines)

    if case in ("quantity", "combined"):
        li = pick()
        v.setdefault("goods_receipt", {})[li["item_no"]] = {"quantity": short_qty(li)}
    if case == "quantity_partial":
        li = pick()
        q = short_qty(li)
        v.setdefault("delivery_note", {})[li["item_no"]] = {"quantity": q}
        v.setdefault("goods_receipt", {})[li["item_no"]] = {"quantity": q}
    if case in ("price", "combined"):
        li = pick()
        new = q2(D(li["unit_price"]) * D(rng.choice(["1.03", "1.05", "1.08", "1.12"])))
        if new == D(li["unit_price"]):
            new += Decimal("0.01")
        v.setdefault("invoice", {}).setdefault(li["item_no"], {})["unit_price"] = s2(new)
    if case == "line_total":
        li = pick()
        delta = D(rng.choice(["9.00", "45.00", "90.00", "100.00"]))
        v.setdefault("invoice", {})[li["item_no"]] = {"line_total": s2(D(li["line_total"]) + delta)}
    if case in ("surcharge", "combined"):
        v["invoice_surcharges"] = [{"label": rng.choice(SURCHARGES[seed_name]),
                                    "amount": s2(D(rng.choice(["65.00", "85.00", "120.00", "150.00", "180.00"])))}]
    if case == "missing_receipt":
        missing = ["goods_receipt"]
    if case == "missing_po":
        missing = ["purchase_order"]
    return v, missing


def ground_truth(pkg_id: str, case: str, m: dict, seed_gt: dict, files: dict, missing: list[str]) -> dict:
    view = doc_view(m)
    po_price = {li["item_no"]: D(li["unit_price"]) for li in view["purchase_order"]}
    has_po, has_gr = "purchase_order" not in missing, "goods_receipt" not in missing
    msa_file, inv_file = files["msa"], files["invoice"]

    def money_lines(rows):
        return [{"item_no": r["item_no"], "quantity": str(r["quantity"]), "unit_price": r["unit_price"],
                 "line_total": r["line_total"]} for r in rows]

    fields = {"invoice": {"invoice_number": m["documents"]["invoice"]["number"],
                          "po_number": m["documents"]["purchase_order"]["number"],
                          "lines": money_lines(view["invoice"]),
                          "surcharges": view["invoice_surcharges"],
                          "tax_rate": str(int(D(m["totals"]["vat_rate_percent"])))}}
    if has_po:
        fields["purchase_order"] = {"po_number": m["documents"]["purchase_order"]["number"],
                                    "lines": money_lines(view["purchase_order"])}
    if has_gr:
        fields["goods_receipt"] = {"receipt_number": m["documents"]["goods_receipt"]["number"],
                                   "po_number": m["documents"]["purchase_order"]["number"],
                                   "lines": [{"item_no": r["item_no"], "quantity": str(r["qty_received"])} for r in view["goods_receipt"]]}
    extra = {"delivery_note": {"number": m["documents"]["delivery_note"]["number"],
                               "lines": [{"item_no": r["item_no"], "quantity": str(r["qty_delivered"])} for r in view["delivery_note"]]}}

    findings = [{"flag": "FLAGGED_MISSING_DOCUMENT", "document_type": doc} for doc in missing]
    received = {r["item_no"]: r["qty_received"] for r in view["goods_receipt"]}
    for r in view["invoice"]:
        qty, price, total = D(r["quantity"]), D(r["unit_price"]), D(r["line_total"])
        if has_gr and qty != received[r["item_no"]]:
            findings.append({"flag": "FLAGGED_QUANTITY_MISMATCH", "error_type": "quantity", "item_no": r["item_no"],
                             "expected": str(received[r["item_no"]]), "actual": str(r["quantity"]),
                             "amount": s2(q2((qty - received[r["item_no"]]) * po_price[r["item_no"]])),
                             "evidence": [{"document": inv_file, "page": 1}, {"document": files["goods_receipt"], "page": 1}]})
        if has_po and price != po_price[r["item_no"]]:
            findings.append({"flag": "FLAGGED_PRICE_MISMATCH", "error_type": "price", "item_no": r["item_no"],
                             "expected": s2(po_price[r["item_no"]]), "actual": r["unit_price"],
                             "amount": s2(q2((price - po_price[r["item_no"]]) * qty)),
                             "evidence": [{"document": inv_file, "page": 1}, {"document": files["purchase_order"], "page": 1}]})
        if total != q2(qty * price):
            findings.append({"flag": "FLAGGED_LINE_TOTAL_MISMATCH", "error_type": "line_total", "item_no": r["item_no"],
                             "expected": s2(q2(qty * price)), "actual": r["line_total"], "amount": s2(total - q2(qty * price)),
                             "evidence": [{"document": inv_file, "page": 1}]})
    sc_clause = seed_gt["msa_clauses"]["surcharge"]
    for sc in view["invoice_surcharges"]:
        findings.append({"flag": "FLAGGED_SURCHARGE", "error_type": "surcharge", "label": sc["label"], "amount": sc["amount"],
                         "evidence": [{"document": inv_file, "page": 1}, {"document": msa_file, "page": sc_clause["page"]}]})

    flags = sorted({f["flag"] for f in findings})
    clauses = {key: {**c, "document": msa_file} for key, c in seed_gt["msa_clauses"].items()}
    return {
        "package_id": pkg_id,
        "seed": m["package_name"],
        "case_type": case,
        "vendor": m["supplier"]["short_name"],
        "buyer": m["buyer"]["name"],
        "supplier": m["supplier"]["name"],
        "documents": {k: v for k, v in files.items() if k in TRANSACTIONAL and k not in missing},
        "contract_documents": {"msa": files["msa"], "purchasing_guideline": files["purchasing_guideline"]},
        "missing_documents": missing,
        "fields": fields,
        "extra_fields": extra,
        "expected_findings": findings,
        "expected_flags": flags,
        "expected_recommendation": ",".join(flags) if flags else "NO_DISCREPANCY",
        "msa_clauses": {"surcharges": {"clause_id": sc_clause["clause"], "document": msa_file, "page": sc_clause["page"],
                                       "text": sc_clause["summary"]}, **clauses},
        "surcharge_relevant": bool(view["invoice_surcharges"]),
        "invoice_totals": view["invoice_totals"],
    }


def register_contracts(seed_mod, library: Path) -> dict[str, str]:
    """Put the seed's MSA and guideline into the contract library under their document numbers."""
    from agent_on_duty import contracts

    cfg, seed_dir = seed_mod.CONFIG, SEEDS_OUT / seed_mod.CONFIG["package_name"]
    names = {"msa": filename(cfg["documents"]["msa"]["number"]),
             "purchasing_guideline": filename(cfg["guideline"]["number"])}
    contracts.add(seed_dir / "msa.pdf", filename=names["msa"], library=library)
    contracts.add(seed_dir / "purchasing_guideline.pdf", filename=names["purchasing_guideline"], library=library)
    return names


def generate(out_dir: Path, seed: int = 42, library: Path | None = None) -> list[dict]:
    from agent_on_duty.contracts import LIBRARY

    library = library or LIBRARY
    rng = random.Random(seed)
    out_dir.mkdir(parents=True, exist_ok=True)
    for old in out_dir.glob("PKG-*"):
        shutil.rmtree(old)
    gts, idx = [], 0
    for seed_mod in SEEDS:
        name = seed_mod.CONFIG["package_name"]
        seed_dir = SEEDS_OUT / name
        seed_gt = json.loads((seed_dir / "ground_truth.json").read_text())
        register_contracts(seed_mod, library)
        for k, case in enumerate(CASES[name], start=1):
            idx += 1
            pkg_id = f"PKG-{idx:03d}"
            m = compute_master(make_config(seed_mod, k, rng))
            variant, missing = inject(case, m, name, rng)
            if variant:
                m["variant"] = variant
            pdir = out_dir / pkg_id
            pdir.mkdir()
            d = m["documents"]
            files = {key: filename(d[key]["number"]) for key in TRANSACTIONAL}
            files["msa"] = filename(d["msa"]["number"])
            files["purchasing_guideline"] = filename(m["guideline"]["number"])
            layout = seed_mod.Layout(m)
            for key in TRANSACTIONAL:
                if key in missing:
                    continue
                spec, meta = getattr(layout, key)()
                render_pdf(pdir / files[key], spec, meta)
            gt = ground_truth(pkg_id, case, m, seed_gt, files, missing)
            (pdir / "ground_truth.json").write_text(json.dumps(gt, indent=1, ensure_ascii=False))
            gts.append(gt)
    return gts
