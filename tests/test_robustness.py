"""Extraction on layouts it was not built for, and the self-check that catches wrong extractions."""

import json

from layouts import english_multipage_invoice, german_invoice

from agent_on_duty import pipeline
from agent_on_duty.extraction.check import check_document, check_package, printed_totals
from agent_on_duty.extraction.extract import DocType, detect_locale, extract_document, extract_package, parse_number


def _lines(doc):
    return {ln.item_no: (ln.quantity, ln.unit_price, ln.line_total) for ln in doc.record.lines}


def test_german_labels_numeric_articles_currency_in_cells(tmp_path):
    truth = german_invoice(tmp_path / "rechnung.pdf")
    doc = extract_document(tmp_path / "rechnung.pdf")
    assert doc.doc_type == DocType.INVOICE
    assert _lines(doc) == {no: (q, p, t) for no, q, p, t in truth["lines"]}
    assert [(s.label, s.amount) for s in doc.record.surcharges] == truth["surcharges"]
    assert printed_totals(tmp_path / "rechnung.pdf") == {"net": truth["net"], "vat": truth["vat"], "gross": truth["gross"]}
    assert check_document(doc, tmp_path / "rechnung.pdf").status == "verified"


def test_english_numbers_over_two_pages(tmp_path):
    truth = english_multipage_invoice(tmp_path / "invoice.pdf")
    doc = extract_document(tmp_path / "invoice.pdf")
    assert len(doc.pages) == 2
    assert _lines(doc) == {no: (q, p, t) for no, q, p, t in truth["lines"]}
    assert check_document(doc, tmp_path / "invoice.pdf").status == "verified"


def test_number_formats():
    assert parse_number("1,234.56", "en") == parse_number("1.234,56", "de")
    assert parse_number("30,00 €") == parse_number("€30,00") == parse_number("30,00")
    assert detect_locale(["1.500", "2.400", "2.54", "4,000", "21.10.2026"]) == "de"
    assert detect_locale(["1,234.56", "12.30", "3,000"]) == "en"


def test_benchmark_packages_all_verified(packages):
    for pdir in packages:
        assert check_package(extract_package(pdir), pdir).status == "verified", pdir.name


def test_self_check_catches_misread_values(packages):
    pdir = packages[0]
    pkg = extract_package(pdir)
    inv = pkg.get(DocType.INVOICE).record
    inv.lines[0].line_total += 1  # a misread amount
    result = check_package(pkg, pdir)
    assert result.status == "uncertain"
    assert any("printed net total" in c.name for c in result.problems)
    pkg = extract_package(pdir)
    pkg.get(DocType.GOODS_RECEIPT).record.lines.pop()  # a missed goods-receipt line
    assert check_package(pkg, pdir).status == "uncertain"


def test_assisted_falls_back_when_uncertain(packages, library, tmp_path, monkeypatch):
    from test_agent import ScriptedModel  # scripted model: no LLM needed

    pdir = packages[0]
    gt = json.loads((pdir / "ground_truth.json").read_text())
    real = pipeline.check_package

    def broken(pkg, d):
        r = real(pkg, d)
        r.status = "uncertain"
        return r

    monkeypatch.setattr(pipeline, "check_package", broken)
    model = ScriptedModel([[("finish", {})]] * 10)
    run, _ = pipeline.verify(pdir, "B", tmp_path / "index", assisted=True, lib=library, client=model)
    assert run.mode == "research" and any("fell back" in n for n in run.notes)
    assert "already extracted" not in model.seen_messages[0][1]["content"]
    assert gt["case_type"]  # package is a real benchmark package
