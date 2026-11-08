"""Completion must reject unresolved required documents; no real model or PDFs needed."""

import pytest

from agent_on_duty.agent.react import SubmitDocumentArgs, Verifier


class FakeRetrieval:
    """Expose a fixed invoice through the same retrieval interface the verifier uses."""

    name = "B"
    tools = [{"function": {"name": "read"}}]

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
