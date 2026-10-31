"""Deterministic calculation tools. The model calls these; it never does arithmetic itself (Exposé §3.3, §5.3)."""

from decimal import Decimal

from agent_on_duty.schemas import Finding, Flag, GoodsReceipt, Invoice, LineItem, PurchaseOrder


def _by_item(lines: list[LineItem]) -> dict[str, LineItem]:
    return {line.item_no: line for line in lines}


def quantity_variance(po: PurchaseOrder, receipt: GoodsReceipt, invoice: Invoice) -> list[Finding]:
    """Invoiced quantity above received quantity, valued at the agreed PO price."""
    po_lines, received = _by_item(po.lines), _by_item(receipt.lines)
    findings = []
    for inv in invoice.lines:
        got = received.get(inv.item_no)
        po_line = po_lines.get(inv.item_no)
        if got is None or po_line is None or inv.quantity == got.quantity:
            continue
        diff = inv.quantity - got.quantity
        findings.append(Finding(
            flag=Flag.QUANTITY_MISMATCH,
            item_no=inv.item_no,
            expected=got.quantity,
            actual=inv.quantity,
            amount=diff * po_line.unit_price,
            formula=f"({inv.quantity} - {got.quantity}) × {po_line.unit_price}",
            evidence=[inv.source, got.source],
        ))
    return findings


def price_variance(po: PurchaseOrder, invoice: Invoice) -> list[Finding]:
    """Invoiced unit price differing from the PO price, over the invoiced quantity."""
    po_lines = _by_item(po.lines)
    findings = []
    for inv in invoice.lines:
        po_line = po_lines.get(inv.item_no)
        if po_line is None or inv.unit_price == po_line.unit_price:
            continue
        diff = inv.unit_price - po_line.unit_price
        findings.append(Finding(
            flag=Flag.PRICE_MISMATCH,
            item_no=inv.item_no,
            expected=po_line.unit_price,
            actual=inv.unit_price,
            amount=diff * inv.quantity,
            formula=f"({inv.unit_price} - {po_line.unit_price}) × {inv.quantity}",
            evidence=[inv.source, po_line.source],
        ))
    return findings


def line_total_variance(invoice: Invoice) -> list[Finding]:
    """Invoice line total not equal to quantity × unit price."""
    findings = []
    for inv in invoice.lines:
        if inv.line_total is None:
            continue
        expected = inv.quantity * inv.unit_price
        if inv.line_total == expected:
            continue
        findings.append(Finding(
            flag=Flag.LINE_TOTAL_MISMATCH,
            item_no=inv.item_no,
            expected=expected,
            actual=inv.line_total,
            amount=inv.line_total - expected,
            formula=f"{inv.line_total} - ({inv.quantity} × {inv.unit_price})",
            evidence=[inv.source],
        ))
    return findings


def total_impact(findings: list[Finding]) -> Decimal:
    return sum((f.amount or Decimal(0) for f in findings), Decimal(0))
