import yaml

from agent_on_duty.extraction.extract import DocType, ExtractedDocument, PageText
from agent_on_duty.retrieval.path_b import _label, _record_concept, _title
from agent_on_duty.schemas import Invoice, SourceRef


def test_record_concept_uses_real_pages_and_skips_empty_fields():
    source = SourceRef(document="invoice.pdf", page=1)
    record = Invoice(invoice_number="INV-1", po_number="", vendor="", lines=[], source=source)
    doc = ExtractedDocument(
        filename="invoice.pdf",
        doc_type=DocType.INVOICE,
        title="",
        pages=[PageText(page=3, text="page 3"), PageText(page=4, text="page 4")],
        record=record,
    )

    concept = _record_concept(doc, [])
    meta = yaml.safe_load(concept.split("---")[1])

    assert meta["page"] == 3
    assert meta["pages"] == [3, 4]
    assert "PO Number" not in concept
    assert "Vendor" not in concept
    assert "**Invoice Number:**" in concept


def test_labels_and_clause_titles_are_human_readable():
    assert _label("po_number") == "PO Number"
    assert _label("tax_rate") == "Tax Rate"
    assert _title("BUYER'S OBLIGATIONS") == "Buyer's Obligations"
    assert _title("EMPLOYEE'S RIGHTS") == "Employee's Rights"
    assert _title("SELLER’S AND BUYER’S DUTIES") == "Seller’s And Buyer’s Duties"
    assert _title("O'BRIEN CLAUSE") == "O'Brien Clause"
