"""Completion must reject unresolved required documents; no real model or PDFs needed."""

import pytest

from agent_on_duty.agent.react import CheckSurchargeArgs, ReportMissingArgs, SubmitDocumentArgs, Verifier


class FakeRetrieval:
    """Expose a fixed invoice through the same retrieval interface the verifier uses."""

    name = "B"
    tools = [{"function": {"name": "read"}}]
    hint = "Open it with read."

    def resolve_document(self, name: str) -> str:
        return name

    def call(self, name, args):
        assert name == "read"
        assert args == {"paths": ["invoice.md"]}
        return (
            "[source: invoice.pdf page 1]\nItem 10: quantity 5, unit price 12.00, line total 60.00",
            {("invoice.pdf", 1)},
        )


def test_finish_rejects_invoice_only_verification():
    verifier = Verifier("PKG-INCOMPLETE", FakeRetrieval())

    # Retrieve first so this test respects the existing evidence guard.
    retrieved = verifier.dispatch("read", {"paths": ["invoice.md"]})
    assert not retrieved.startswith("Error")
    verifier.submit_document(SubmitDocumentArgs(
        doc_type="invoice",
        document="invoice.pdf",
        lines=[{"item_no": "10", "quantity": "5", "unit_price": "12.00", "line_total": "60.00"}],
    ))

    # Invoice arithmetic is correct, but the PO and goods receipt are unresolved.
    result = verifier.run_checks()
    assert verifier.checks_ran
    assert verifier.findings == []
    assert "purchase_order" in result and "goods_receipt" in result
    assert set(verifier.docs) == {"invoice"}
    assert verifier.missing == set()

    # Safe completion must reject this state and explain both outstanding documents.
    with pytest.raises(ValueError) as error:
        verifier.finish()

    assert "purchase_order" in str(error.value)
    assert "goods_receipt" in str(error.value)
    assert verifier.run.recommendation is None
    assert verifier.done is False


DOCS = [{"file": "invoice.pdf"}, {"file": "PO-1.pdf"}, {"file": "MSA-X-01.pdf"}]


def test_submit_rejects_package_document_not_retrieved():
    verifier = Verifier("PKG-UNSEEN", FakeRetrieval(), documents=DOCS)
    verifier.dispatch("read", {"paths": ["invoice.md"]})

    # PO-1.pdf belongs to the package but was never retrieved (only quoted on the invoice).
    with pytest.raises(ValueError) as error:
        verifier.submit_document(SubmitDocumentArgs(
            doc_type="purchase_order", document="PO-1.pdf",
            lines=[{"item_no": "10", "quantity": "5", "unit_price": "12.00"}]))
    assert "not been retrieved" in str(error.value)
    assert "Open it with read." in str(error.value)


def _with_invoice(verifier, surcharges=()):
    verifier.dispatch("read", {"paths": ["invoice.md"]})
    verifier.submit_document(SubmitDocumentArgs(
        doc_type="invoice", document="invoice.pdf", surcharges=list(surcharges),
        lines=[{"item_no": "10", "quantity": "5", "unit_price": "12.00", "line_total": "60.00"}]))
    return verifier


def test_clause_document_without_extension_maps_to_package_file():
    verifier = _with_invoice(Verifier("PKG-MSA", FakeRetrieval(), documents=DOCS),
                             [{"label": "Energy surcharge", "amount": "85.00"}])
    verifier.seen.add(("MSA-X-01.pdf", 9))

    verifier.check_surcharge(CheckSurchargeArgs(label="Energy surcharge", amount="85,00",
                                                clause_document="MSA-X-01", clause_page=9))
    assert verifier.run.cited_clauses[0]["document"] == "MSA-X-01.pdf"
    assert verifier.surcharge_findings[0].amount == 85


def test_submit_rejects_values_not_printed_in_document():
    verifier = Verifier("PKG-NUM", FakeRetrieval(), documents=DOCS)
    verifier.dispatch("read", {"paths": ["invoice.md"]})
    verifier.texts["invoice.pdf"] = "Pos. 1 PV-KS-4030 Tape 2.400 roll 1,38 3.312,00"

    with pytest.raises(ValueError) as error:  # unit price copied from elsewhere
        verifier.submit_document(SubmitDocumentArgs(
            doc_type="invoice", document="invoice.pdf",
            lines=[{"item_no": "PV-KS-4030", "quantity": "2400", "unit_price": "1.45", "line_total": "3312.00"}]))
    assert "unit_price 1.45" in str(error.value)
    assert "shows: Pos. 1 PV-KS-4030 Tape 2.400 roll 1,38 3.312,00" in str(error.value)

    # German and English formats of the printed values are both accepted
    verifier.submit_document(SubmitDocumentArgs(
        doc_type="invoice", document="invoice.pdf",
        lines=[{"item_no": "PV-KS-4030", "quantity": "2400", "unit_price": "1,38", "line_total": "3312.00"}]))


def test_submit_rejects_document_retrieved_in_same_response():
    verifier = Verifier("PKG-TURN", FakeRetrieval(), documents=DOCS)
    verifier._turn_seen = set()  # a model response begins with nothing retrieved
    verifier.dispatch("read", {"paths": ["invoice.md"]})
    with pytest.raises(ValueError) as error:
        verifier.submit_document(SubmitDocumentArgs(
            doc_type="invoice", document="invoice.pdf",
            lines=[{"item_no": "10", "quantity": "5", "unit_price": "12.00", "line_total": "60.00"}]))
    assert "same response" in str(error.value)


def test_check_surcharge_rejects_surcharge_not_on_invoice():
    verifier = _with_invoice(Verifier("PKG-NOSC", FakeRetrieval(), documents=DOCS))
    verifier.seen.add(("MSA-X-01.pdf", 9))
    with pytest.raises(ValueError) as error:
        verifier.check_surcharge(CheckSurchargeArgs(label="10.58", amount="10.58",
                                                    clause_document="MSA-X-01.pdf", clause_page=9))
    assert "no surcharges" in str(error.value)
    assert verifier.surcharge_findings == []


def test_finish_requires_invoice_surcharge_checked():
    verifier = _with_invoice(Verifier("PKG-SC", FakeRetrieval()), [{"label": "Freight", "amount": "63.92"}])
    verifier.report_missing(ReportMissingArgs(doc_type="purchase_order"))
    verifier.report_missing(ReportMissingArgs(doc_type="goods_receipt"))
    verifier.run_checks()
    with pytest.raises(ValueError) as error:
        verifier.finish()
    assert "Freight" in str(error.value)


def test_run_checks_rejects_partial_goods_receipt():
    verifier = _with_invoice(Verifier("PKG-PART", FakeRetrieval()))
    verifier.docs["invoice"].lines.append(verifier.docs["invoice"].lines[0].model_copy(update={"item_no": "20"}))
    verifier.texts["gr.pdf"] = "Goods receipt  10  5 received   20  3 received"
    verifier.seen.add(("gr.pdf", 1))
    verifier.submit_document(SubmitDocumentArgs(doc_type="goods_receipt", document="gr.pdf",
                                                lines=[{"item_no": "10", "quantity": "5"}]))
    with pytest.raises(ValueError) as error:
        verifier.run_checks()
    assert "goods_receipt: 20" in str(error.value)
    assert not verifier.checks_ran
