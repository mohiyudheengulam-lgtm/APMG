"""Generic build pipeline for a seed package: master data -> PDFs -> verification -> ground truth."""

from __future__ import annotations

from collections import Counter
from decimal import Decimal
from pathlib import Path

import pymupdf

from common import (
    D,
    SEEDS_OUT,
    VerificationError,
    de_date,
    de_num,
    dump_json,
    find_clause_page,
    iban_grouped,
    norm_ws,
    pdf_text,
    preview,
    render_pdf,
    require,
    row_numbers,
)

TRANSACTIONAL = ("purchase_order", "delivery_note", "goods_receipt", "invoice")


def _check_row(path: Path, item_no: str, expected: list[Decimal], errors: list[str]) -> None:
    try:
        nums = row_numbers(path, item_no)
    except VerificationError as exc:
        errors.append(str(exc))
        return
    pool = Counter(nums)
    for e in expected:
        if pool[e] > 0:
            pool[e] -= 1
        else:
            errors.append(f"{path.name}: row {item_no}: expected value {e} not found in {nums}")


def verify(m: dict, layout, out: Path) -> list[str]:
    """Open every PDF, extract text, and compare against master data. Raises on mismatch."""
    errors: list[str] = []
    b, s, d, t = m["buyer"], m["supplier"], m["documents"], m["totals"]
    money = layout.money
    texts = {name: "\n".join(pdf_text(out / f"{name}.pdf")) for name in TRANSACTIONAL + ("msa", "purchasing_guideline")}

    common_party = [b["name"], s["name"]]
    # --- purchase order (buyer)
    tx = texts["purchase_order"]
    for need in common_party + [
        d["purchase_order"]["number"], de_date(d["purchase_order"]["date"]), d["msa"]["number"],
        de_date(d["purchase_order"]["requested_delivery_date"]), b["vat_id"], iban_grouped(b["bank"]["iban"]),
        b["registration"]["number"], money(t["net_total"]), money(t["vat_amount"]), money(t["gross_total"]),
    ]:
        require(tx, need, "purchase_order", errors)
    # --- delivery note (supplier)
    tx = texts["delivery_note"]
    for need in common_party + [
        d["delivery_note"]["number"], de_date(d["delivery_note"]["date"]), d["purchase_order"]["number"],
        s["vat_id"], iban_grouped(s["bank"]["iban"]), s["registration"]["number"], d["delivery_note"]["packages"],
    ]:
        require(tx, need, "delivery_note", errors)
    # --- goods receipt (buyer internal)
    tx = texts["goods_receipt"]
    for need in [
        b["name"], s["name"], d["goods_receipt"]["number"], de_date(d["goods_receipt"]["date"]),
        d["purchase_order"]["number"], d["delivery_note"]["number"], d["goods_receipt"]["receiving_clerk"],
    ]:
        require(tx, need, "goods_receipt", errors)
    # --- invoice (supplier)
    tx = texts["invoice"]
    inv = d["invoice"]
    for need in common_party + [
        inv["number"], de_date(inv["date"]), de_date(inv["due_date"]), de_date(inv["discount_deadline"]),
        d["purchase_order"]["number"], d["delivery_note"]["number"], d["msa"]["number"],
        b["vat_id"], s["vat_id"], iban_grouped(s["bank"]["iban"]), s["bank"]["bic"], s["registration"]["number"],
        money(t["net_total"]), money(t["vat_amount"]), money(t["gross_total"]),
        money(t["early_payment_discount_amount"]), money(t["amount_payable_within_discount_period"]),
        f"{de_num(t['vat_rate_percent'], 0)} %", f"{de_num(t['early_payment_discount_percent'], 0)} %",
    ]:
        require(tx, need, "invoice", errors)
    if "surcharge" in tx.lower() or "zuschlag" in tx.lower():
        errors.append("invoice: clean package must not mention any surcharge")

    # --- line items, row by row
    for li in m["line_items"]:
        qty, price, total = D(li["quantity"]), D(li["unit_price"]), D(li["line_total"])
        _check_row(out / "purchase_order.pdf", li["item_no"], [qty, price, total], errors)
        _check_row(out / "invoice.pdf", li["item_no"], [qty, price, total], errors)
        _check_row(out / "delivery_note.pdf", li["item_no"], [qty, qty], errors)  # ordered + delivered
        _check_row(out / "goods_receipt.pdf", li["item_no"], [qty, qty, qty], errors)  # ordered, per DN, received
    # --- arithmetic re-check from the *rendered* invoice
    inv_path = out / "invoice.pdf"
    rendered_totals = []
    for li in m["line_items"]:
        nums = row_numbers(inv_path, li["item_no"])
        q, p = D(li["quantity"]), D(li["unit_price"])
        if q in nums and p in nums:
            rendered_totals.append((q * p).quantize(Decimal("0.01")))
    if sum(rendered_totals) != D(t["net_total"]):
        errors.append(f"invoice: recomputed net {sum(rendered_totals)} != {t['net_total']}")

    # --- MSA: parties, number, terms, price-list annex
    tx = texts["msa"]
    pt = m["msa_terms"]["payment_terms"]
    for need in [
        b["name"], s["name"], d["msa"]["number"], de_date(d["msa"]["signing_date"]),
        f"{pt['net_days']} days net", f"{de_num(pt['early_payment_discount_percent'], 0)} %",
        f"within {pt['discount_days']} days", de_date(m["msa_terms"]["price_lock"]["end_date"]),
        f"{m['msa_terms']['price_lock']['months']} months", m["msa_terms"]["late_delivery_penalty"]["rate_text"],
        m["msa_terms"]["late_delivery_penalty"]["cap_text"],
    ]:
        require(tx, need, "msa", errors)
    for p in m["price_list"]:
        _check_row(out / "msa.pdf", p["item_no"], [D(p["unit_price"])], errors)
    for li in m["line_items"]:
        if not any(p["item_no"] == li["item_no"] and p["unit_price"] == li["unit_price"] for p in m["price_list"]):
            errors.append(f"master: order line {li['item_no']} not on MSA price list at same price")

    # --- guideline
    tx = texts["purchasing_guideline"]
    for need in [b["name"], "three-way match", "zero tolerance"]:
        if norm_ws(need).lower() not in norm_ws(tx).lower():
            errors.append(f"purchasing_guideline: missing {need!r}")

    # no on-page 'synthetic' marker, but metadata must carry it
    for name in texts:
        if "synthetic" in texts[name].lower():
            errors.append(f"{name}: the word 'synthetic' must only be in metadata, not on the page")
        doc = pymupdf.open(str(out / f"{name}.pdf"))
        if "synthetic test data" not in (doc.metadata.get("subject") or ""):
            errors.append(f"{name}: metadata subject lacks 'synthetic test data'")
        if doc[0].rect != pymupdf.paper_rect("a4"):
            errors.append(f"{name}: not A4")
        doc.close()

    if errors:
        raise VerificationError("Verification failed:\n  - " + "\n  - ".join(errors))
    return errors


def build(pkg) -> dict:
    from common import compute_master

    m = compute_master(pkg.CONFIG)
    out = SEEDS_OUT / m["package_name"]
    out.mkdir(parents=True, exist_ok=True)
    dump_json(out / "master_data.json", m)

    layout = pkg.Layout(m)
    pages = {}
    for name in TRANSACTIONAL + ("purchasing_guideline",):
        spec, meta = getattr(layout, name)()
        pages[name] = render_pdf(out / f"{name}.pdf", spec, meta)
    spec, meta, key_clauses = layout.msa()
    pages["msa"] = render_pdf(out / "msa.pdf", spec, meta)
    if hasattr(layout, "msa_toc"):  # two-pass layout: table of contents with real page numbers
        toc = None
        for _ in range(4):
            new_toc = layout.msa_toc(out / "msa.pdf")
            if new_toc == toc:
                break
            toc = new_toc
            spec, meta, key_clauses = layout.msa(toc_pages=toc)
            pages["msa"] = render_pdf(out / "msa.pdf", spec, meta)
        else:
            raise VerificationError("MSA table of contents did not stabilise")

    for name in pages:
        preview(out / f"{name}.pdf", m["package_name"])

    verify(m, layout, out)

    clause_gt = {}
    for key, info in key_clauses.items():
        loc = find_clause_page(out / "msa.pdf", info["search_label"], info["opening"])
        clause_gt[key] = {
            "clause": info["clause"],
            "clause_title": info["clause_title"],
            "page": loc["page"],
            "msa_page_count": loc["page_count"],
            "summary": info["summary"],
        }
    half = pages["msa"] / 2
    if not clause_gt["surcharge"]["page"] > half:
        raise VerificationError(f"surcharge clause on page {clause_gt['surcharge']['page']} is not in 2nd half")
    if not 14 <= pages["msa"] <= 16:
        raise VerificationError(f"MSA has {pages['msa']} pages (expected 14-16)")
    if not 2 <= pages["purchasing_guideline"] <= 3:
        raise VerificationError(f"guideline has {pages['purchasing_guideline']} pages (expected 2-3)")

    gt = ground_truth(m, pages, clause_gt)
    dump_json(out / "ground_truth.json", gt)
    return {"package": m["package_name"], "pages": pages, "clauses": clause_gt, "gross": m["totals"]["gross_total"]}


def ground_truth(m: dict, pages: dict, clauses: dict) -> dict:
    b, s, d, t = m["buyer"], m["supplier"], m["documents"], m["totals"]
    party = lambda p: {"name": p["name"], "vat_id": p["vat_id"]}  # noqa: E731
    lines = m["line_items"]
    po_lines = [{k: li[k] for k in ("position", "item_no", "description", "unit", "quantity", "unit_price", "line_total")} for li in lines]
    return {
        "package": m["package_name"],
        "data_origin": "synthetic test data",
        "currency": m["currency"],
        "expected_recommendation": "NO_DISCREPANCY",
        "expected_flags": [],
        "documents": {
            "purchase_order": {
                "file": "purchase_order.pdf", "pages": pages["purchase_order"],
                "header": {
                    "po_number": d["purchase_order"]["number"], "po_date": d["purchase_order"]["date"],
                    "msa_number": d["msa"]["number"], "requested_delivery_date": d["purchase_order"]["requested_delivery_date"],
                    "issuer": party(b), "recipient": party(s),
                },
                "line_items": po_lines,
                "totals": {k: t[k] for k in ("net_total", "vat_rate_percent", "vat_amount", "gross_total")},
            },
            "delivery_note": {
                "file": "delivery_note.pdf", "pages": pages["delivery_note"],
                "header": {
                    "delivery_note_number": d["delivery_note"]["number"], "delivery_date": d["delivery_note"]["date"],
                    "po_number": d["purchase_order"]["number"], "issuer": party(s), "recipient": party(b),
                    "packages": d["delivery_note"]["packages"],
                },
                "line_items": [{"item_no": li["item_no"], "unit": li["unit"], "quantity_ordered": li["quantity"], "quantity_delivered": li["quantity"]} for li in lines],
            },
            "goods_receipt": {
                "file": "goods_receipt.pdf", "pages": pages["goods_receipt"],
                "header": {
                    "goods_receipt_number": d["goods_receipt"]["number"], "receipt_date": d["goods_receipt"]["date"],
                    "po_number": d["purchase_order"]["number"], "delivery_note_number": d["delivery_note"]["number"],
                    "receiving_clerk": d["goods_receipt"]["receiving_clerk"], "issuer": party(b), "supplier": party(s),
                },
                "line_items": [{"item_no": li["item_no"], "unit": li["unit"], "quantity_ordered": li["quantity"], "quantity_received": li["quantity"]} for li in lines],
            },
            "invoice": {
                "file": "invoice.pdf", "pages": pages["invoice"],
                "header": {
                    "invoice_number": d["invoice"]["number"], "invoice_date": d["invoice"]["date"],
                    "due_date": d["invoice"]["due_date"], "discount_deadline": d["invoice"]["discount_deadline"],
                    "po_number": d["purchase_order"]["number"], "delivery_note_number": d["delivery_note"]["number"],
                    "msa_number": d["msa"]["number"], "issuer": party(s), "recipient": party(b),
                    "supplier_iban": s["bank"]["iban"],
                },
                "line_items": po_lines,
                "surcharges": [],
                "totals": t,
            },
            "msa": {"file": "msa.pdf", "pages": pages["msa"], "number": d["msa"]["number"], "signing_date": d["msa"]["signing_date"]},
            "purchasing_guideline": {"file": "purchasing_guideline.pdf", "pages": pages["purchasing_guideline"]},
        },
        "calculations": {
            "line_totals": [
                {"item_no": li["item_no"], "formula": f"{li['quantity']} x {li['unit_price']}", "line_total": li["line_total"]}
                for li in lines
            ],
            "net_total": t["net_total"],
            "vat": {"rate_percent": t["vat_rate_percent"], "formula": f"{t['net_total']} x 0.19 (ROUND_HALF_UP)", "amount": t["vat_amount"]},
            "gross_total": t["gross_total"],
            "early_payment_discount": {
                "percent": t["early_payment_discount_percent"], "base": "gross_total",
                "amount": t["early_payment_discount_amount"], "payable_if_paid_by_deadline": t["amount_payable_within_discount_period"],
            },
            "three_way_match": [
                {
                    "item_no": li["item_no"], "po_quantity": li["quantity"], "received_quantity": li["quantity"],
                    "invoiced_quantity": li["quantity"], "po_unit_price": li["unit_price"],
                    "msa_unit_price": li["unit_price"], "invoiced_unit_price": li["unit_price"], "match": True,
                }
                for li in lines
            ],
            "surcharges_total": "0.00",
        },
        "msa_clauses": {
            "price_lock": clauses["price_lock"],
            "surcharge": clauses["surcharge"],
            "payment_terms": clauses["payment_terms"],
            "late_delivery_penalty": clauses["penalty"],
        },
    }
