"""Pydantic schemas shared by extraction, both retrieval paths, the agent and the audit engine (Exposé §4, §5)."""

from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    """Where a value or clause came from. A citation is correct only if document and page both match (§6.3)."""

    document: str
    page: int = Field(ge=1)


class LineItem(BaseModel):
    item_no: str
    description: str
    quantity: Decimal = Field(ge=0)
    unit_price: Decimal | None = None  # goods receipts carry no price
    line_total: Decimal | None = None
    source: SourceRef


class PurchaseOrder(BaseModel):
    po_number: str
    vendor: str
    currency: str = "EUR"
    lines: list[LineItem]
    source: SourceRef


class GoodsReceipt(BaseModel):
    receipt_number: str
    po_number: str
    lines: list[LineItem]
    source: SourceRef


class Surcharge(BaseModel):
    label: str
    amount: Decimal
    source: SourceRef


class Invoice(BaseModel):
    invoice_number: str
    po_number: str
    vendor: str
    currency: str = "EUR"
    lines: list[LineItem]
    surcharges: list[Surcharge] = []
    source: SourceRef


class MSAClause(BaseModel):
    clause_id: str
    topic: str  # e.g. pricing, surcharges, payment_terms
    text: str
    source: SourceRef


class Flag(StrEnum):
    PRICE_MISMATCH = "FLAGGED_PRICE_MISMATCH"
    QUANTITY_MISMATCH = "FLAGGED_QUANTITY_MISMATCH"
    SURCHARGE = "FLAGGED_SURCHARGE"
    MISSING_DOCUMENT = "FLAGGED_MISSING_DOCUMENT"


class Finding(BaseModel):
    flag: Flag
    item_no: str | None = None
    expected: Decimal | None = None
    actual: Decimal | None = None
    amount: Decimal | None = None  # monetary impact
    formula: str | None = None
    evidence: list[SourceRef] = Field(min_length=1)


class Recommendation(BaseModel):
    """Agent output. Empty findings == NO_DISCREPANCY. The agent never writes a final decision."""

    package_id: str
    findings: list[Finding] = []

    @property
    def label(self) -> str:
        return "NO_DISCREPANCY" if not self.findings else ",".join(sorted({f.flag for f in self.findings}))


class ReviewState(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    REVIEWED = "REVIEWED"


class Decision(StrEnum):
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    OVERRIDDEN = "OVERRIDDEN"


class ManagerDecision(BaseModel):
    decision: Decision
    reviewer: str
    timestamp: datetime
    override_reason: str | None = None
