"""Extraction must reproduce every ground-truth field of the generated benchmark exactly."""

import json
from pathlib import Path

import pytest

from agent_on_duty.benchmark.generator import generate
from agent_on_duty.extraction.extract import DocType, extract_package


@pytest.fixture(scope="module")
def packages(tmp_path_factory):
    out = tmp_path_factory.mktemp("packages")
    generate(out, seed=42)
    return sorted(p for p in out.iterdir() if p.is_dir())


def _lines(record):
    return [{k: str(v) for k, v in ln.model_dump(include={"item_no", "quantity", "unit_price", "line_total"}).items()
             if v is not None} for ln in record.lines]


def test_fields_match_ground_truth(packages):
    for pdir in packages:
        gt = json.loads((pdir / "ground_truth.json").read_text())
        ex = extract_package(pdir)
        for doc_type, expected in gt["fields"].items():
            doc = ex.get(DocType(doc_type))
            assert doc is not None, (pdir.name, doc_type)
            assert _lines(doc.record) == expected["lines"], (pdir.name, doc_type)
        inv = ex.get(DocType.INVOICE).record
        assert [{"label": s.label, "amount": str(s.amount)} for s in inv.surcharges] == \
            [{"label": s["label"], "amount": s["amount"]} for s in gt["fields"]["invoice"]["surcharges"]]
        assert str(inv.tax_rate) == gt["fields"]["invoice"]["tax_rate"]
        for missing in gt["missing_documents"]:
            assert ex.get(DocType(missing)) is None


def test_msa_pages(packages):
    ex = extract_package(packages[0])
    msa = ex.get(DocType.MSA)
    assert msa.record is None and len(msa.pages) >= 14
    assert "Surcharges" in msa.pages[13].text
