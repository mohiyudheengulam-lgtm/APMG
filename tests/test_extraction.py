"""Extraction must reproduce every ground-truth field of the generated benchmark, across both seed layouts."""

import json
from decimal import Decimal

from agent_on_duty.extraction.extract import DocType, extract_package, parse_number
from agent_on_duty.retrieval.path_b import _msa_sections


def test_german_numbers():
    assert parse_number("1.234,56") == Decimal("1234.56")
    assert parse_number("1.200") == Decimal("1200")
    assert parse_number("0,42") == Decimal("0.42")
    assert parse_number("-3") == Decimal("-3")
    assert parse_number("4,000 V") is None


def test_document_types(packages):
    for pdir in packages:
        gt = json.loads((pdir / "ground_truth.json").read_text())
        ex = extract_package(pdir)
        got = {d.filename: d.doc_type.value for d in ex.documents}
        want = {f: ("guideline" if k == "purchasing_guideline" else k) for k, f in gt["documents"].items()}
        assert got == want, pdir.name


def test_fields_match_ground_truth(packages):
    for pdir in packages:
        gt = json.loads((pdir / "ground_truth.json").read_text())
        ex = extract_package(pdir)
        for doc_type, expected in gt["fields"].items():
            rec = ex.get(DocType(doc_type)).record
            got = [{k: str(getattr(ln, k)) for k in ("item_no", "quantity", "unit_price", "line_total") if getattr(ln, k) is not None}
                   for ln in rec.lines]
            want = [{k: str(Decimal(v)) if k != "item_no" else v for k, v in ln.items()} for ln in expected["lines"]]
            assert got == want, (pdir.name, doc_type)
        inv = ex.get(DocType.INVOICE).record
        assert [(s.label, s.amount) for s in inv.surcharges] == \
            [(s["label"], Decimal(s["amount"])) for s in gt["fields"]["invoice"]["surcharges"]], pdir.name
        assert str(inv.tax_rate) == gt["fields"]["invoice"]["tax_rate"]
        dn = ex.get(DocType.DELIVERY_NOTE).record
        assert [(ln.item_no, str(ln.quantity)) for ln in dn.lines] == \
            [(ln["item_no"], ln["quantity"]) for ln in gt["extra_fields"]["delivery_note"]["lines"]], pdir.name


def test_msa_sections_cite_clause_pages(packages):
    for pdir in (packages[0], packages[-1]):  # one package per seed
        gt = json.loads((pdir / "ground_truth.json").read_text())
        msa = extract_package(pdir).get(DocType.MSA)
        sections = _msa_sections(msa)
        assert len(sections) > 30
        for key in ("surcharge", "price_lock", "payment_terms", "late_delivery_penalty"):
            clause = gt["msa_clauses"][key]
            number = clause["clause"].split("(")[0].split(".")[0].strip()  # "27.2" -> "27", "§ 28 (2)" -> "§ 28"
            sec = next(s for s in sections if s["clause_id"] == number)
            text = "\n".join(sec["lines"])
            marker = text.rfind("[page", 0, text.find(clause["clause"].split(" (")[-1].rstrip(")") if "(" in clause["clause"] else clause["clause"]))
            assert f"[page {clause['page']}]" == text[marker:text.index("]", marker) + 1], (key, clause)
