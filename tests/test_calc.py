"""The worked example from Exposé §1: 500 ordered @ 12.00, 480 received, invoiced 500 @ 12.40 + 150 fuel surcharge → EUR 590."""

from decimal import Decimal as D

from agent_on_duty.schemas import (
    Finding, Flag, GoodsReceipt, Invoice, LineItem, PurchaseOrder, SourceRef, Surcharge,
)
from agent_on_duty.tools.calc import line_total_variance, price_variance, quantity_variance, total_impact

PO_REF = SourceRef(document="PO-1001.pdf", page=1)
GR_REF = SourceRef(document="GR-1001.pdf", page=1)
INV_REF = SourceRef(document="INV-1001.pdf", page=1)
MSA_REF = SourceRef(document="MSA-ACME.pdf", page=14)

po = PurchaseOrder(po_number="PO-1001", vendor="ACME", source=PO_REF, lines=[
    LineItem(item_no="10", description="Widget", quantity=D(500), unit_price=D("12.00"), source=PO_REF),
])
receipt = GoodsReceipt(receipt_number="GR-1001", po_number="PO-1001", source=GR_REF, lines=[
    LineItem(item_no="10", description="Widget", quantity=D(480), source=GR_REF),
])
invoice = Invoice(invoice_number="INV-1001", po_number="PO-1001", vendor="ACME", source=INV_REF, lines=[
    LineItem(item_no="10", description="Widget", quantity=D(500), unit_price=D("12.40"),
             line_total=D("6200.00"), source=INV_REF),
], surcharges=[Surcharge(label="fuel surcharge", amount=D(150), source=INV_REF)])


def test_quantity_variance():
    [f] = quantity_variance(po, receipt, invoice)
    assert f.flag == Flag.QUANTITY_MISMATCH
    assert f.amount == D("240.00")


def test_price_variance():
    [f] = price_variance(po, invoice)
    assert f.flag == Flag.PRICE_MISMATCH
    assert f.amount == D("200.00")


def test_line_total_consistent():
    assert line_total_variance(invoice) == []


def test_example_totals_590():
    surcharge = Finding(flag=Flag.SURCHARGE, amount=D(150), evidence=[INV_REF, MSA_REF])
    findings = quantity_variance(po, receipt, invoice) + price_variance(po, invoice) + [surcharge]
    assert total_impact(findings) == D("590.00")


def test_line_total_flag():
    bad = invoice.model_copy(update={"lines": [invoice.lines[0].model_copy(update={"line_total": D("6300.00")})]})
    [f] = line_total_variance(bad)
    assert f.flag == Flag.LINE_TOTAL_MISMATCH and f.amount == D("100.00")
