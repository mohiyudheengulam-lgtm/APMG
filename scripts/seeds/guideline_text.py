"""Content of the buyer's internal purchasing guideline (shared prose, per-package values).

Returns a list of ``(title, html_body)`` sections; each package layout styles them.
CSS classes used: ``tbl`` (table), ``num`` (right-aligned cell), ``note`` (callout box).
"""

from __future__ import annotations


def guideline_sections(g: dict) -> list[tuple[str, str]]:
    th = g["thresholds"]
    rows = "".join(
        f"<tr><td>{t['range']}</td><td>{t['approver']}</td><td>{t['form']}</td></tr>" for t in th
    )
    roles = "".join(f"<tr><td><b>{r[0]}</b></td><td>{r[1]}</td></tr>" for r in g["roles"])
    return [
        (
            "Purpose and Scope",
            f"<p>This guideline governs the procurement of production materials, operating supplies and indirect "
            f"materials by {g['buyer_name']} and the subsequent verification and approval of supplier invoices. It "
            f"applies to all employees involved in requisitioning, ordering, receiving goods, and checking or "
            f"approving invoices, at all sites of the company.</p>"
            f"<p>Where a framework agreement (master supply agreement, MSA) exists with a supplier, the terms of that "
            f"agreement take precedence over the supplier’s offers and standard terms. Purchasing staff must check "
            f"for an applicable framework agreement before every order and must quote its number on the purchase order.</p>",
        ),
        (
            "Approval Thresholds for Purchase Orders and Invoices",
            f"<p>Purchase orders and supplier invoices must be approved in accordance with the following thresholds. "
            f"The decisive value is the <b>gross</b> amount of the order or invoice in EUR. Splitting an order or "
            f"invoice in order to stay below a threshold is prohibited.</p>"
            f"<table class='tbl'><tr><th>Gross amount</th><th>Required approval</th><th>Form of approval</th></tr>{rows}</table>"
            f"<p>Approvals are given in the ERP workflow; signatures on paper are accepted only during system outages "
            f"and must be entered into the system within two working days.</p>",
        ),
        (
            "Three-Way Matching Requirement",
            "<p>No supplier invoice for goods may be released for payment unless it has been successfully matched "
            "against three documents (three-way match):</p>"
            "<ol><li>the <b>purchase order</b> issued by the Purchasing Department (item, quantity, agreed unit price);</li>"
            "<li>the <b>goods receipt</b> posted by the central warehouse (quantity actually received, referencing the "
            "supplier’s delivery note); and</li>"
            "<li>the <b>supplier invoice</b> (invoiced item, quantity, unit price, line totals, VAT and gross total).</li></ol>"
            "<p>In addition, the agreed prices and commercial terms of the applicable MSA (price list, price lock, "
            "surcharge rules and payment terms) must be checked. Every invoice must reference the purchase order number; "
            "invoices without a valid purchase order reference are returned to the supplier.</p>"
            "<p>Line totals, net total, VAT and gross total of the invoice must be recalculated. Arithmetic differences "
            "are treated as discrepancies regardless of the amount.</p>",
        ),
        (
            "Tolerance Rules",
            "<table class='tbl'><tr><th>Check</th><th>Tolerance</th><th>Action if exceeded</th></tr>"
            "<tr><td>Unit price invoice vs. purchase order / MSA price list</td><td><b>0.00 EUR (zero tolerance)</b></td><td>Block invoice, clarify with supplier via Purchasing</td></tr>"
            "<tr><td>Surcharges, fees or additional charges not pre-approved in writing by Purchasing (incl. fuel and energy surcharges)</td><td><b>Zero tolerance</b></td><td>Block invoice, request credit note</td></tr>"
            "<tr><td>Invoiced quantity vs. quantity received</td><td>Invoiced quantity must not exceed received quantity</td><td>Block invoice, clarify with warehouse and supplier</td></tr>"
            "<tr><td>Line total, net total, VAT and gross total (recalculation)</td><td>0.00 EUR</td><td>Block invoice, request corrected invoice</td></tr>"
            "<tr><td>Missing purchase order, delivery note or goods receipt</td><td>Not permitted</td><td>Hold invoice until documents are complete</td></tr>"
            "</table>"
            "<div class='note'>Unapproved surcharges and price deviations are never paid “for the sake of simplicity”, "
            "even if the amount is small. Approval of a surcharge exists only if a written approval of the Purchasing "
            "Department for the specific order is on file.</div>",
        ),
        (
            "Invoice Approval Responsibilities",
            f"<table class='tbl'><tr><th>Role</th><th>Responsibility</th></tr>{roles}</table>"
            "<p>The person who issued a purchase order may not be the sole approver of the invoice relating to it "
            "(four-eyes principle). Approvers confirm with their approval that the three-way match and the MSA check "
            "have been completed without discrepancy or that every discrepancy has been resolved and documented.</p>",
        ),
        (
            "Early-Payment Discounts and Payment Runs",
            f"<p>Early-payment discounts agreed in framework agreements must be used whenever an invoice has been "
            f"approved within the discount period. Accounts Payable schedules approved invoices for the next payment "
            f"run ({g['payment_runs']}) before the discount deadline. Lost discounts caused by late approval are "
            f"reported monthly to the Head of Purchasing.</p>",
        ),
        (
            "Documentation and Retention",
            "<p>All documents of the three-way match, approvals, clarification notes and credit notes are filed "
            "with the invoice in the document management system and retained in accordance with the statutory "
            "retention periods (ten years for invoices and accounting records).</p>",
        ),
    ]
