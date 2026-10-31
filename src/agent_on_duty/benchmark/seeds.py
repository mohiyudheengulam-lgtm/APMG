"""Seed templates (Exposé §7.1 step 1): two vendors, their catalogues and MSA wording.

Vendor ACME prohibits every surcharge; vendor NORD permits a capped freight surcharge.
Section order differs between the two MSAs so clause pages are not trivially predictable.
"""

FILLER = (
    "The Parties shall perform their obligations under this Agreement in good faith and with the care "
    "customary in the trade. Any notice under this section shall be given in writing and shall become "
    "effective upon receipt by the other Party. Obligations that by their nature are intended to survive "
    "expiry or termination of this Agreement shall survive. Headings are for convenience only and do not "
    "affect interpretation. Where this Agreement refers to a period of days, calendar days are meant unless "
    "business days are expressly specified. The Supplier shall maintain records sufficient to demonstrate "
    "compliance with this section for a period of six years. "
)

ACME = {
    "code": "ACME",
    "name": "ACME Industrial Supplies GmbH",
    "buyer": "Nubitech Manufacturing AG",
    "catalogue": [
        ("A-100", "Hex bolt M8x40, zinc plated"),
        ("A-110", "Hex nut M8, grade 8"),
        ("A-200", "Bearing 6204-2RS"),
        ("A-310", "Hydraulic hose 1/2 inch, per metre"),
        ("A-420", "Safety gloves, cut level D"),
        ("A-500", "Cable tie 300 mm, pack of 100"),
    ],
    "surcharge_policy": "prohibited",
    "freight_cap": None,
    # (clause_id, topic, title, body); pricing body gets the rate card appended
    "sections": [
        ("1", "definitions", "Definitions", "In this Agreement, 'Goods' means the products listed in the Rate Card; 'Order' means a purchase order issued by the Buyer; 'Invoice' means the Supplier's request for payment."),
        ("2", "scope", "Scope of Agreement", "This Master Service Agreement governs all Orders placed by the Buyer with the Supplier during its term."),
        ("3", "ordering", "Ordering Procedure", "Orders shall be issued in writing and shall state item number, quantity and the agreed unit price."),
        ("4", "pricing", "Prices and Rate Card", "Unit prices for the Goods are fixed as set out in the Rate Card below and are locked for a period of twelve (12) months from the Effective Date. No price escalation applies during this period unless agreed in a written amendment signed by both Parties."),
        ("5", "delivery", "Delivery", "Delivery shall be made DAP Buyer's warehouse. Title passes on acceptance of the Goods."),
        ("6", "acceptance", "Inspection and Acceptance", "The Buyer shall record received quantities in a goods receipt. Only accepted quantities may be invoiced."),
        ("7", "invoicing", "Invoicing", "Each Invoice shall reference exactly one Order and shall bill only quantities recorded as received."),
        ("8", "payment_terms", "Payment Terms", "Payment is due thirty (30) days net from receipt of a correct Invoice. The Buyer may deduct a two percent (2%) early-payment discount if payment is made within ten (10) days."),
        ("9", "penalties", "Late Delivery Penalties", "For each full week of delay, the Supplier shall pay a penalty of 0.5% of the delayed Order value, capped at 5%."),
        ("10", "warranty", "Warranty", "The Supplier warrants that the Goods are free from defects in material and workmanship for twelve months."),
        ("11", "liability", "Liability", "Neither Party shall be liable for indirect or consequential loss except in cases of wilful misconduct."),
        ("12", "confidentiality", "Confidentiality", "Each Party shall keep the terms of this Agreement, including all prices, confidential."),
        ("13", "audit", "Audit Rights", "The Buyer may audit the Supplier's invoicing records once per calendar year on reasonable notice."),
        ("14", "surcharges", "Surcharges and Ancillary Charges", "The Supplier shall not invoice any surcharge or ancillary charge, including but not limited to fuel, freight, energy, handling or small-quantity surcharges, unless such charge has been pre-approved in writing by the Buyer's procurement manager. Invoices containing charges without such approval will be rejected in respect of those charges."),
        ("15", "term", "Term and Termination", "This Agreement has an initial term of twenty-four months and renews automatically for twelve-month periods."),
        ("16", "law", "Governing Law", "This Agreement is governed by the laws of the Federal Republic of Germany."),
    ],
}

NORD = {
    "code": "NORD",
    "name": "Nordlicht Laborbedarf KG",
    "buyer": "Nubitech Manufacturing AG",
    "catalogue": [
        ("N-010", "Nitrile gloves, size M, box of 100"),
        ("N-020", "Pipette tips 200 ul, rack of 96"),
        ("N-035", "Sample bottle 500 ml, HDPE"),
        ("N-048", "Lab coat, polycotton, size L"),
        ("N-060", "Isopropanol 70%, 5 L"),
        ("N-075", "Filter paper, 125 mm, pack of 100"),
    ],
    "surcharge_policy": "freight_capped",
    "freight_cap": 100,
    "sections": [
        ("1", "definitions", "Definitions", "Capitalised terms have the meaning given in this section. 'Goods' means laboratory consumables listed in Schedule A."),
        ("2", "scope", "Scope", "This Framework Agreement applies to all purchases of Goods by the Buyer from the Supplier."),
        ("3", "pricing", "Pricing (Schedule A)", "The unit prices in Schedule A below are binding for the term of this Agreement and may only be changed by written amendment."),
        ("4", "ordering", "Orders", "Orders become binding upon written confirmation by the Supplier within two business days."),
        ("5", "surcharges", "Freight and Other Charges", "The Supplier may invoice a freight surcharge not exceeding EUR 100.00 per Invoice for deliveries to the Buyer's laboratory sites. Any other surcharge, including fuel, energy, packaging or handling surcharges, and any freight surcharge above EUR 100.00, requires the Buyer's prior written approval."),
        ("6", "delivery", "Delivery and Packaging", "Goods shall be delivered in original manufacturer packaging, temperature-controlled where required."),
        ("7", "acceptance", "Goods Receipt", "Quantities are deemed accepted as recorded on the Buyer's goods receipt."),
        ("8", "invoicing", "Invoices", "Invoices shall reference the Buyer's Order number and list each item with quantity, unit price and line total."),
        ("9", "payment_terms", "Payment", "Payment is due within forty-five (45) days. A three percent (3%) discount applies to payment within fourteen (14) days."),
        ("10", "quality", "Quality Assurance", "The Supplier maintains an ISO 9001 certified quality management system."),
        ("11", "warranty", "Warranty", "Defective Goods shall be replaced free of charge within five business days of notification."),
        ("12", "liability", "Liability", "Liability is limited to the value of the affected Order except for personal injury."),
        ("13", "confidentiality", "Confidentiality", "Commercial terms including Schedule A are confidential."),
        ("14", "term", "Term", "This Agreement runs for thirty-six months from the Effective Date."),
    ],
}

SEEDS = {"ACME": ACME, "NORD": NORD}
