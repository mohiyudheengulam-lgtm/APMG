"""Seed package 2: Quentrion Elektronik GmbH (buyer) <- Sarvelin Components GmbH (supplier).

Electronic components. Deliberately different visual language from package 1:
serif typography, burgundy header band (buyer) / teal side stripe + grid tables (supplier),
monospace WMS printout for the goods receipt, SAP-style numbering (positions 10/20/..),
"EUR 1.234,56" money format, German "§ 9 (3)" clause numbering and a table of contents in the MSA.
All companies, people, addresses, VAT IDs, IBANs and phone numbers are fictional
(phone numbers use the Bundesnetzagentur ranges reserved for fictional use).
"""

from __future__ import annotations

import re
from datetime import date, timedelta

import pymupdf

from common import (
    doc_view,
    PageDecor, RenderSpec, de_date, de_num, esc, htmlbox, iban_checksum, iban_grouped, pdf_date,
)
from guideline_text import guideline_sections
from msa_clauses import annex_kpis, build_clauses, clause_index, escalation


def _add_days(iso: str, n: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=n)).isoformat()


MSA_EFFECTIVE = "2026-03-01"
INVOICE_DATE = "2026-10-23"
NET_DAYS, DISC_DAYS = 45, 10

_ITEMS = {
    "SC-C0603-104X50": ("Multilayer ceramic capacitor 100 nF, 50 V, X7R, case 0603, reel of 4,000", "reel", "9.60"),
    "SC-R0603-10K0F": ("Thick-film chip resistor 10 kOhm, 1 %, 0.1 W, case 0603, reel of 5,000", "reel", "4.25"),
    "SC-MCU-M4-512L64": ("32-bit microcontroller, M4 core, 512 KB flash, 128 KB RAM, LQFP-64", "pcs", "4.87"),
    "SC-LDO-33-SOT223": ("LDO voltage regulator 3.3 V, 500 mA, SOT-223", "pcs", "0.32"),
    "SC-HDR-2X10-254": ("Pin header 2 x 10 pins, pitch 2.54 mm, THT, gold-plated", "pcs", "0.21"),
    "SC-USBC-16SMT": ("USB Type-C receptacle, 16 pins, SMT, mid-mount", "pcs", "0.58"),
    "SC-XTL-16M-3225": ("Quartz crystal 16.000 MHz, 12 pF load, 3.2 x 2.5 mm SMD", "pcs", "0.27"),
    "SC-ECAP-470U25": ("Aluminium electrolytic capacitor 470 µF, 25 V, 105 °C, 10 x 12.5 mm", "pcs", "0.14"),
    "SC-C0402-105X16": ("Multilayer ceramic capacitor 1 µF, 16 V, X5R, case 0402, reel of 10,000", "reel", "7.90"),
    "SC-TVS-SMBJ24A": ("TVS diode 24 V, 600 W, unidirectional, SMB package", "pcs", "0.19"),
    "SC-FB-0805-600R": ("Ferrite bead 600 Ohm at 100 MHz, 1 A, case 0805, reel of 4,000", "reel", "11.40"),
}
_ORDER = [("SC-C0603-104X50", 20), ("SC-R0603-10K0F", 30), ("SC-MCU-M4-512L64", 1500), ("SC-LDO-33-SOT223", 3000),
          ("SC-HDR-2X10-254", 2000), ("SC-USBC-16SMT", 1500), ("SC-XTL-16M-3225", 1500), ("SC-ECAP-470U25", 2500)]

CONFIG = {
    "package_name": "seed_02_electronic_components",
    "description": "Clean package: electronic components, all documents consistent.",
    "currency": "EUR",
    "vat_rate": "19",
    "position_step": 10,
    "buyer": {
        "name": "Quentrion Elektronik GmbH",
        "short_name": "Quentrion",
        "address": {"street": "Ellerbrockweg 9", "postal_code": "50829", "city": "Köln", "country": "Germany"},
        "vat_id": "DE271609384",
        "registration": {"court": "Amtsgericht Köln", "number": "HRB 109452"},
        "managing_directors": ["Markus Vellinger", "Dr. Anja Klee"],
        "phone": "+49 221 4710-500",
        "email": "procurement@quentrion-elektronik.de",
        "website": "www.quentrion-elektronik.de",
        "contact": {"name": "Daniel Ostendorf", "role": "Commodity Buyer Electronics, Strategic Procurement",
                    "phone": "+49 221 4710-537", "email": "d.ostendorf@quentrion-elektronik.de"},
        "accounts_payable": {"name": "Ingrid Sauerwein", "email": "invoices@quentrion-elektronik.de"},
        "bank": {"bank_name": "Domstadt Kreditbank AG", "iban": iban_checksum("DE", "37061877" + "2093318405"), "bic": "DSKRDEK1XXX"},
        "warehouse": {"name": "Central Warehouse, Hall 4 – Goods-In", "street": "Ellerbrockweg 13", "postal_code": "50829",
                      "city": "Köln", "receiving_hours": "06:30 and 14:30"},
        "supplier_number_for_supplier": "300417",
    },
    "supplier": {
        "name": "Sarvelin Components GmbH",
        "short_name": "Sarvelin",
        "address": {"street": "Lindwurmring 30", "postal_code": "60528", "city": "Frankfurt am Main", "country": "Germany"},
        "vat_id": "DE305882471",
        "tax_number": "045 228 61094",
        "registration": {"court": "Amtsgericht Frankfurt am Main", "number": "HRB 127604"},
        "managing_directors": ["Florian Haberkamp", "Nadine Esch"],
        "phone": "+49 69 90009-400",
        "email": "orders@sarvelin-components.de",
        "website": "www.sarvelin-components.de",
        "contact": {"name": "Tobias Reinhold", "role": "Account Manager Industrial",
                    "phone": "+49 69 90009-428", "email": "t.reinhold@sarvelin-components.de"},
        "dispatch_contact": "Merve Yildiz",
        "bank": {"bank_name": "Mainfeld Privatbank AG", "iban": iban_checksum("DE", "50061922" + "0071458830"), "bic": "MFPBDEFFXXX"},
        "customer_number_for_buyer": "D-0028815",
    },
    "documents": {
        "msa": {"number": "RV-QE-SC/2026/003", "signing_date": "2026-02-24", "effective_date": MSA_EFFECTIVE},
        "purchase_order": {"number": "4500021873", "date": "2026-10-12", "requested_delivery_date": "2026-10-22"},
        "delivery_note": {"number": "DN/2610/00487", "date": "2026-10-21", "packages": "4 cartons",
                          "gross_weight_kg": "38.6"},
        "goods_receipt": {"number": "5000184227", "date": "2026-10-22", "receiving_clerk": "Svenja Kowalczyk",
                          "storage_location": "H4-ESD"},
        "invoice": {"number": "IN26-118904", "date": INVOICE_DATE,
                    "due_date": _add_days(INVOICE_DATE, NET_DAYS),
                    "discount_deadline": _add_days(INVOICE_DATE, DISC_DAYS)},
    },
    "msa_terms": {
        "payment_terms": {"net_days": NET_DAYS, "early_payment_discount_percent": "3", "discount_days": DISC_DAYS,
                          "discount_base": "gross invoice amount"},
        "price_lock": {"months": 12, "start_date": MSA_EFFECTIVE, "end_date": "2027-02-28"},
        "surcharge_rule": "Surcharges of any kind (incl. fuel/energy surcharges) are not permitted unless approved "
                          "in advance and in writing by the Buyer's Purchasing Department for the specific order.",
        "late_delivery_penalty": {"rate_percent": "0.3", "per": "each commenced Business Day",
                                  "cap_percent": "6", "basis": "net order value of the delayed goods",
                                  "rate_text": "0.3 %", "cap_text": "6 %"},
        "incoterm": "DAP",
        "lead_time_business_days": 8,
        "warranty_months": 36,
        "governing_law": "Germany (CISG excluded)",
        "jurisdiction": "Cologne",
        "initial_term": "two (2) years",
        "termination_notice": "three (3) months’",
    },
    "price_list": [{"item_no": k, "description": v[0], "unit": v[1], "unit_price": v[2]} for k, v in _ITEMS.items()],
    "order_items": [{"item_no": k, "description": _ITEMS[k][0], "unit": _ITEMS[k][1], "quantity": q, "unit_price": _ITEMS[k][2]}
                    for k, q in _ORDER],
    "guideline": {
        "number": "QE-PROC-POL-011", "version": "2.0", "valid_from": "2026-04-01", "owner": "Head of Strategic Procurement",
        "approved_by": "Markus Vellinger, CEO, and Dr. Anja Klee, CFO", "payment_runs": "every Wednesday",
        "thresholds": [
            {"range": "up to 2,500.00", "approver": "Team lead of the requesting cost centre", "form": "Workflow approval"},
            {"range": "2,500.01 – 15,000.00", "approver": "Head of Strategic Procurement", "form": "Workflow approval"},
            {"range": "15,000.01 – 75,000.00", "approver": "Head of Strategic Procurement and CFO", "form": "Workflow, two signatures"},
            {"range": "above 75,000.00", "approver": "Both managing directors", "form": "Board memo + workflow"},
        ],
        "roles": [
            ("Strategic Procurement", "Owns supplier framework agreements and price lists, issues purchase orders, is the only function entitled to approve surcharges in writing, clarifies price discrepancies."),
            ("Goods-In / Central Warehouse", "Counts and inspects deliveries (incl. ESD and moisture-sensitive packaging), posts goods receipts referencing the delivery note, documents shortfalls."),
            ("Accounts Payable", "Registers invoices, executes the three-way match and recalculation, blocks invoices with discrepancies and routes them to Strategic Procurement."),
            ("Cost centre approver", "Approves invoices within the thresholds of section 2 once the three-way match is clean."),
            ("Head of Strategic Procurement", "Decides on escalated discrepancies; documents any exception to this policy in writing."),
        ],
    },
}

WINE, WINE_LIGHT, GOLD = "#7a1f3d", "#f7eef2", "#a07a3f"
TEAL, TEAL_LIGHT, ORANGE, INK = "#00695c", "#e3f1ef", "#d9730d", "#263238"


def money(v) -> str:
    return f"EUR {de_num(v)}"


class Layout:
    def __init__(self, m: dict):
        self.m = m
        self.b, self.s, self.d = m["buyer"], m["supplier"], m["documents"]
        self.t = m["totals"]
        self._toc_pages: dict[int, int] | None = None

    money = staticmethod(money)

    # ================================================================== buyer (Quentrion) chrome
    def _buyer_band(self, title: str):
        b = self.b

        def header(page: pymupdf.Page, n: int, total: int):
            w = page.rect.width
            page.draw_rect(pymupdf.Rect(0, 0, w, 64), color=None, fill=(0.478, 0.122, 0.239))
            page.draw_rect(pymupdf.Rect(0, 64, w, 67), color=None, fill=(0.627, 0.478, 0.247))
            htmlbox(page, (48, 16, 330, 60),
                    "<div style='font-family:serif;color:white'><span style='font-size:20pt;font-weight:bold'>Q U E N T R I O N</span><br/>"
                    "<span style='font-size:7.5pt'>ELEKTRONIK GMBH &nbsp;·&nbsp; EMS &amp; Industrial Electronics</span></div>")
            htmlbox(page, (330, 22, w - 48, 58),
                    f"<div style='font-family:serif;color:white;text-align:right;font-size:13pt;font-style:italic'>{title}</div>")

        return header

    def _buyer_footer(self, extra: str = ""):
        b = self.b

        def footer(page: pymupdf.Page, n: int, total: int):
            r = page.rect
            mds = ", ".join(b["managing_directors"])
            html = (
                "<div style='font-family:serif;font-size:6.8pt;color:#6b5a60;text-align:center;line-height:1.5'>"
                f"{esc(b['name'])} | {b['address']['street']} | {b['address']['postal_code']} {b['address']['city']} | Tel. {b['phone']} | {b['website']}<br/>"
                f"Registered office Köln | {b['registration']['court']} {b['registration']['number']} | Managing Directors: {mds} | VAT ID {b['vat_id']}<br/>"
                f"{b['bank']['bank_name']} | IBAN {iban_grouped(b['bank']['iban'])} | BIC {b['bank']['bic']}</div>"
            )
            page.draw_line((48, r.height - 62), (r.width - 48, r.height - 62), color=(0.627, 0.478, 0.247), width=0.6)
            htmlbox(page, (40, r.height - 58, r.width - 40, r.height - 18), html)
            htmlbox(page, (r.width - 200, r.height - 16, r.width - 48, r.height - 4),
                    f"<div style='font-family:serif;font-size:6.5pt;color:#6b5a60;text-align:right'>{extra}{n}/{total}</div>")

        return footer

    # ================================================================== supplier (Sarvelin) chrome
    def _supplier_header(self, page: pymupdf.Page, n: int, total: int):
        h = page.rect.height
        page.draw_rect(pymupdf.Rect(0, 0, 16, h), color=None, fill=(0.0, 0.412, 0.361))
        page.draw_rect(pymupdf.Rect(0, 60, 16, 92), color=None, fill=(0.851, 0.451, 0.051))

    def _supplier_footer(self):
        s = self.s

        def footer(page: pymupdf.Page, n: int, total: int):
            r = page.rect
            page.draw_line((44, r.height - 66), (r.width - 40, r.height - 66), color=(0.0, 0.412, 0.361), width=1.2)
            mds = ", ".join(s["managing_directors"])
            html = (
                "<table style='width:100%;font-family:serif;font-size:6.6pt;color:#37474f;line-height:1.45'><tr>"
                f"<td style='vertical-align:top;padding-right:6px'>{esc(s['name'])}<br/>{s['address']['street']}<br/>{s['address']['postal_code']} {s['address']['city']}</td>"
                f"<td style='vertical-align:top;border-left:0.6px solid #00695c;padding:0 6px'>Phone {s['phone']}<br/>{s['email']}<br/>{s['website']}</td>"
                f"<td style='vertical-align:top;border-left:0.6px solid #00695c;padding:0 6px'>{s['registration']['court']}<br/>{s['registration']['number']}<br/>Managing Directors: {mds}</td>"
                f"<td style='vertical-align:top;border-left:0.6px solid #00695c;padding-left:6px'>{s['bank']['bank_name']}<br/>IBAN {iban_grouped(s['bank']['iban'])}<br/>BIC {s['bank']['bic']} · VAT ID {s['vat_id']}</td>"
                "</tr></table>"
            )
            htmlbox(page, (44, r.height - 62, r.width - 40, r.height - 20), html)
            htmlbox(page, (r.width - 160, r.height - 18, r.width - 40, r.height - 6),
                    f"<div style='font-family:serif;font-size:6.5pt;color:#00695c;text-align:right'>Page {n} of {total}</div>")

        return footer

    def _supplier_logo(self, title: str) -> str:
        return (
            "<table style='width:100%'><tr>"
            f"<td style='vertical-align:top'><span style='font-size:21pt;font-weight:bold;color:{TEAL}'>Sarvelin</span>"
            f"<span style='font-size:21pt;font-weight:bold;color:{ORANGE}'>.</span><br/>"
            f"<span style='font-size:8pt;font-style:italic;color:{TEAL}'>components · distribution · logistics</span></td>"
            f"<td style='text-align:right;vertical-align:top;font-size:20pt;color:#90a4ae'>{title}</td></tr></table>"
        )

    def _ref_grid(self, cells: list[tuple[str, str]]) -> str:
        rows = ""
        for i in range(0, len(cells), 2):
            pair = cells[i : i + 2]
            rows += "<tr>" + "".join(
                f"<td class='gk' width='19%'>{k}</td><td class='gv' width='31%'>{v}</td>" for k, v in pair
            ) + "</tr>"
        return f"<table class='grid'>{rows}</table>"

    # ================================================================== purchase order (buyer)
    def purchase_order(self):
        m, b, s, d, t = self.m, self.b, self.s, self.d, self.t
        po = d["purchase_order"]
        w = b["warehouse"]
        pt = m["msa_terms"]["payment_terms"]
        rows = "".join(
            f"<tr class='{'z' if i % 2 else ''}'><td>{li['position']:03d}</td><td class='ino'>{li['item_no']}</td>"
            f"<td>{esc(li['description'])}</td><td class='r'>{de_num(li['quantity'], 0)}</td><td>{li['unit']}</td>"
            f"<td class='r'>{de_num(li['unit_price'])}</td><td class='r'>{de_num(li['line_total'])}</td></tr>"
            for i, li in enumerate(m["line_items"])
        )
        strip = "".join(
            f"<td style='width:{wd}px;vertical-align:top;padding:4px 6px;border-left:2px solid {GOLD}'>"
            f"<div class='sl'>{k}</div><div class='sv'>{v}</div></td>"
            for wd, k, v in [
                (76, "PO NUMBER", po["number"]), (64, "ORDER DATE", de_date(po["date"])),
                (108, "FRAMEWORK AGREEMENT", d["msa"]["number"]), (60, "SUPPLIER NO.", b["supplier_number_for_supplier"]),
                (118, "BUYER / DIRECT DIAL", f"{b['contact']['name']}<br/>{b['contact']['phone']}"),
            ]
        )
        html = f"""
        <table><tr>
          <td style='width:250px;vertical-align:top'><div class='sl'>SUPPLIER</div>
            <div style='font-size:10.5pt;line-height:1.35'>{esc(s['name'])}<br/>Attn. {s['contact']['name']}<br/>{s['address']['street']}<br/>{s['address']['postal_code']} {s['address']['city']}</div></td>
          <td style='width:249px;vertical-align:top'><div class='sl'>DELIVER TO</div>
            <div style='font-size:10.5pt;line-height:1.35'>{esc(b['name'])}<br/>{w['name']}<br/>{w['street']}<br/>{w['postal_code']} {w['city']}</div></td>
        </tr></table>
        <table style='margin-top:14px;background-color:{WINE_LIGHT}'><tr>{strip}</tr></table>
        <h1>Purchase Order No. {po['number']}</h1>
        <p>Please supply the items below in accordance with framework agreement {d['msa']['number']}. Each reel, tray and
        carton must be labelled with our PO number and position. Order acknowledgement is requested within two business days to
        {b['contact']['email']}.</p>
        <table class='items'>
          <tr><th>Pos.</th><th>Your item no.</th><th>Description</th><th class='r'>Quantity</th><th>UoM</th><th class='r'>Price/UoM</th><th class='r'>Net value</th></tr>
          {rows}
        </table>
        <table style='width:100%;margin-top:8px'><tr><td width='50%'></td><td width='50%'>
          <table class='tot'>
            <tr><td>Total net value</td><td class='r'>{money(t['net_total'])}</td></tr>
            <tr><td>VAT {de_num(t['vat_rate_percent'], 0)} %</td><td class='r'>{money(t['vat_amount'])}</td></tr>
            <tr class='g'><td>Total order value</td><td class='r'>{money(t['gross_total'])}</td></tr>
          </table></td></tr></table>
        <h3>Delivery and commercial terms</h3>
        <p class='terms'><b>Delivery date:</b> {de_date(po['requested_delivery_date'])}, goods-in Mon–Fri {w['receiving_hours'].replace(' and ', '–')} ·
        <b>Incoterms® 2020:</b> {m['msa_terms']['incoterm']} Köln · <b>Payment:</b> {pt['net_days']} days net or
        {de_num(pt['early_payment_discount_percent'], 0)} % discount within {pt['discount_days']} days ·
        <b>Packaging:</b> ESD-safe, MSL devices in dry packs per J-STD-033 · <b>Invoices:</b> {b['accounts_payable']['email']}, quoting PO no. and delivery note no.</p>
        <p class='small'>The terms of framework agreement {d['msa']['number']} apply exclusively. Additional charges or surcharges
        will not be accepted without the prior written approval of Strategic Procurement.</p>
        <table style='width:100%;margin-top:14px'><tr>
          <td width='50%'>{esc(b['name'])}<br/>Strategic Procurement<br/><br/><i>{b['contact']['name']}</i></td>
          <td width='50%' style='text-align:right;vertical-align:bottom;font-size:7.5pt;color:#6b5a60'>Electronically released – valid without signature</td>
        </tr></table>
        """
        css = f"""
        body {{font-family:serif;font-size:9.4pt;color:#2b2326}}
        h1 {{font-size:14pt;color:{WINE};margin:16px 0 6px 0;font-weight:normal}}
        h3 {{font-size:9.5pt;color:{WINE};margin:10px 0 3px 0}}
        p {{margin:0 0 6px 0;line-height:1.4}}
        p.terms {{font-size:8.6pt;line-height:1.5}}
        p.small {{font-size:7.8pt;color:#6b5a60}}
        div.sl {{font-size:6.8pt;color:{GOLD};letter-spacing:0.5px}}
        div.sv {{font-size:8.6pt;font-weight:bold}}
        table.items {{width:100%;border-collapse:collapse;font-size:8.3pt}}
        table.items th {{color:{WINE};text-align:left;padding:4px 3px;border-top:0.8px solid {WINE};border-bottom:2.2px double {WINE};white-space:nowrap}}
        table.items td {{padding:4px 3px;vertical-align:top}}
        tr.z td {{background-color:{WINE_LIGHT}}}
        td.ino {{white-space:nowrap;font-size:7.8pt}}
        .r {{text-align:right}} table.items th.r {{text-align:right}}
        table.tot {{width:100%;border-collapse:collapse;font-size:9.2pt}}
        table.tot td {{padding:2px 3px}}
        table.tot tr.g td {{font-weight:bold;color:{WINE};border-top:0.8px solid {WINE};border-bottom:2.2px double {WINE}}}
        """
        spec = RenderSpec([html], css, top=86, bottom=74, left=48, right=48,
                          decor=PageDecor(header=self._buyer_band("Purchase Order"), footer=self._buyer_footer("Page ")))
        return spec, {"title": f"Purchase Order {po['number']}", "author": b["name"], "keywords": "purchase order",
                      "creationDate": pdf_date(po["date"])}

    # ================================================================== delivery note (supplier)
    def delivery_note(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        dn = d["delivery_note"]
        w = b["warehouse"]
        rows = "".join(
            f"<tr><td class='c'>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td>"
            f"<td class='c'>{li['unit']}</td><td class='r'>{de_num(li['qty_ordered'], 0)}</td><td class='r'><b>{de_num(li['qty_delivered'], 0)}</b></td>"
            f"<td class='c'>{2626 + i}-{'A' if i % 2 else 'B'}</td></tr>"
            for i, li in enumerate(doc_view(m)["delivery_note"])
        )
        ship_note = (f"<b>Shipment complete.</b> No open quantities remain on purchase order {d['purchase_order']['number']}."
                     if doc_view(m)["dn_complete"] else
                     f"<b>Partial shipment.</b> Open quantities on purchase order {d['purchase_order']['number']} will follow as a separate delivery.")
        grid = self._ref_grid([
            ("Delivery note", dn["number"]), ("Ship date", de_date(dn["date"])),
            ("Customer PO", d["purchase_order"]["number"]), ("PO date", de_date(d["purchase_order"]["date"])),
            ("Customer no.", s["customer_number_for_buyer"]), ("Packages", dn["packages"]),
            ("Gross weight", f"{dn['gross_weight_kg'].replace('.', ',')} kg"), ("Shipping", f"{m['msa_terms']['incoterm']} Köln, parcel carrier"),
        ])
        html = f"""
        {self._supplier_logo('DELIVERY NOTE')}
        <div style='height:10px'></div>
        {grid}
        <table style='width:100%;margin-top:12px'><tr>
          <td width='50%' style='vertical-align:top'><div class='lbl'>Ship to</div>
            <div class='addr'>{esc(b['name'])}<br/>{w['name']}<br/>{w['street']}<br/>{w['postal_code']} {w['city']}</div></td>
          <td width='50%' style='vertical-align:top'><div class='lbl'>Sold to</div>
            <div class='addr'>{esc(b['name'])}<br/>{b['address']['street']}<br/>{b['address']['postal_code']} {b['address']['city']}</div></td>
        </tr></table>
        <p style='margin-top:12px'>Contents shipped against your purchase order {d['purchase_order']['number']}. ESD-sensitive goods –
        open only at ESD-protected workstations. Moisture-sensitive devices are dry-packed (bag seal date {de_date(dn['date'])}).</p>
        <table class='items'>
          <tr><th class='c'>PO pos.</th><th>Item no.</th><th>Description</th><th class='c'>UoM</th><th class='r'>Ordered</th><th class='r'>Shipped</th><th class='c'>Date code</th></tr>
          {rows}
        </table>
        <p style='margin-top:10px'>{ship_note}
        Certificates of conformance are enclosed in carton 1/4.</p>
        <table style='width:100%;margin-top:28px;font-size:8pt'><tr>
          <td width='45%' style='border-top:0.8px solid {TEAL};padding-top:3px'>Packed and checked: {s['dispatch_contact']}, Sarvelin logistics</td>
          <td width='10%'></td>
          <td width='45%' style='border-top:0.8px solid {TEAL};padding-top:3px'>Received in good order (date / signature)</td>
        </tr></table>
        """
        spec = RenderSpec([html], self._supplier_css(), top=40, bottom=80, left=44, right=40,
                          decor=PageDecor(header=self._supplier_header, footer=self._supplier_footer()))
        return spec, {"title": f"Delivery Note {dn['number']}", "author": s["name"], "keywords": "delivery note",
                      "creationDate": pdf_date(dn["date"])}

    @staticmethod
    def _supplier_css() -> str:
        return f"""
        body {{font-family:serif;font-size:9.2pt;color:{INK}}}
        p {{margin:0 0 6px 0;line-height:1.4}}
        div.lbl {{font-size:7pt;color:{ORANGE};font-weight:bold}}
        div.addr {{font-size:10pt;line-height:1.35}}
        table.grid {{width:100%;border-collapse:collapse;font-size:8.4pt}}
        table.grid td {{border:0.6px solid {TEAL};padding:3px 5px}}
        td.gk {{background-color:{TEAL_LIGHT};color:{TEAL}}}
        td.gv {{font-weight:bold}}
        table.items {{width:100%;border-collapse:collapse;font-size:8.2pt}}
        table.items th {{background-color:{TEAL_LIGHT};color:{TEAL};border:0.6px solid {TEAL};padding:4px 3px;text-align:left;white-space:nowrap}}
        table.items td {{border:0.6px solid #80b4ad;padding:4px 3px;vertical-align:top}}
        td.ino {{white-space:nowrap;font-size:7.8pt}}
        .r {{text-align:right}} .c {{text-align:center}} table.items th.r {{text-align:right}} table.items th.c {{text-align:center}}
        table.tot {{width:100%;border-collapse:collapse;font-size:9pt}}
        table.tot td {{border:0.6px solid {TEAL};padding:3px 5px}}
        table.tot tr.g td {{background-color:{TEAL};color:white;font-weight:bold}}
        div.pay {{border:0.8px dashed {ORANGE};padding:6px 8px;font-size:8.4pt;line-height:1.5;margin-top:12px}}
        """

    # ================================================================== goods receipt (buyer WMS printout)
    def goods_receipt(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        gr = d["goods_receipt"]
        rows = "".join(
            f"<tr><td>{li['position']:04d}</td><td class='ino'>{li['item_no']}</td><td>{li['unit'].upper()}</td>"
            f"<td class='r'>{de_num(li['qty_ordered'], 0)}</td><td class='r'>{de_num(li['qty_delivered'], 0)}</td><td class='r'>{de_num(li['qty_received'], 0)}</td>"
            f"<td class='r'>{de_num(li['qty_received'] - li['qty_delivered'], 0)}</td><td>{gr['storage_location']}-{(i % 4) + 1:02d}</td>"
            f"<td>{'QI-FREE' if li['qty_received'] == li['qty_delivered'] else 'BLOCKED'}</td></tr>"
            for i, li in enumerate(doc_view(m)["goods_receipt"])
        )
        view = doc_view(m)
        shortfall = "NO" if not view["gr_short_items"] else "YES"
        end_note = ("no deviations" if view["gr_clean"] else
                    f"deviations: {', '.join(view['gr_short_items'])} short" if view["gr_short_items"] else "partial delivery per DN")
        html = f"""
        <div class='h'>QUENTRION ELEKTRONIK GMBH :: WMS GOODS RECEIPT POSTING</div>
        <div class='sub'>Material document {gr['number']} / {date.fromisoformat(gr['date']).year} &nbsp; Mvt type 101 &nbsp; Plant 1000 Köln &nbsp; Storage location {gr['storage_location']}</div>
        <table class='f'>
          <tr><td width='24%'>MATERIAL DOC.</td><td width='26%'>{gr['number']}</td><td width='24%'>POSTING DATE</td><td width='26%'>{de_date(gr['date'])}</td></tr>
          <tr><td>PURCHASE ORDER</td><td>{d['purchase_order']['number']}</td><td>DOCUMENT DATE</td><td>{de_date(d['delivery_note']['date'])}</td></tr>
          <tr><td>DELIVERY NOTE</td><td>{d['delivery_note']['number']}</td><td>PACKAGES</td><td>{d['delivery_note']['packages']}</td></tr>
          <tr><td>VENDOR</td><td>{b['supplier_number_for_supplier']}</td><td>VENDOR NAME</td><td>{esc(s['name'])}</td></tr>
          <tr><td>RECEIVED BY</td><td>{gr['receiving_clerk']}</td><td>USER ID</td><td>SKOWALCZ</td></tr>
        </table>
        <table class='items'>
          <tr><th>ITEM</th><th>MATERIAL / VENDOR PART</th><th>UOM</th><th class='r'>PO QTY</th><th class='r'>DN QTY</th><th class='r'>RECEIVED</th><th class='r'>DIFF</th><th>BIN</th><th>STOCK</th></tr>
          {rows}
        </table>
        <div class='sep'>--- incoming checks ---</div>
        <table class='f'>
          <tr><td width='50%'>ESD packaging intact ........... YES</td><td width='50%'>MSL dry packs sealed / HIC ok ... YES</td></tr>
          <tr><td>Labels match delivery note ..... YES</td><td>Certificate of conformance ...... YES</td></tr>
          <tr><td>Quantity check (count/weigh) ... {'OK' if not view['gr_short_items'] else 'SHORT'}</td><td>Damage / shortfall reported ..... {shortfall}</td></tr>
        </table>
        <div class='sep'>--- end of goods receipt {gr['number']} : {len(m['line_items'])} items posted, {end_note} ---</div>
        <table style='width:100%;margin-top:26px'><tr>
          <td width='45%' style='border-top:0.6px dashed #333;padding-top:3px'>Goods-In clerk: {gr['receiving_clerk']}</td><td width='10%'></td>
          <td width='45%' style='border-top:0.6px dashed #333;padding-top:3px'>Stock placement confirmed: Hall 4 / {gr['storage_location']}</td>
        </tr></table>
        """
        css = """
        body {font-family:monospace;font-size:8pt;color:#111}
        div.h {font-size:10.5pt;font-weight:bold;border-top:1.5px solid #111;border-bottom:1.5px solid #111;padding:3px 0}
        div.sub {font-size:7.5pt;margin:3px 0 10px 0}
        table.f {width:100%;border-collapse:collapse;margin-bottom:10px}
        table.f td {padding:2px 2px}
        table.items {width:100%;border-collapse:collapse;font-size:7.6pt}
        table.items th {text-align:left;border-top:0.8px dashed #111;border-bottom:0.8px dashed #111;padding:3px 5px;white-space:nowrap}
        table.items td {padding:3px 5px;border-bottom:0.4px dotted #888}
        td.ino {white-space:nowrap}
        .r {text-align:right} table.items th.r {text-align:right}
        div.sep {margin:10px 0 6px 0;font-size:7.6pt}
        """
        gr_dt = de_date(gr["date"])
        spec = RenderSpec([html], css, top=86, bottom=74, left=48, right=48,
                          decor=PageDecor(header=self._buyer_band("Goods Receipt – internal"),
                                          footer=self._buyer_footer(f"WMS print {gr_dt} 08:14 · SKOWALCZ · page ")))
        return spec, {"title": f"Goods Receipt {gr['number']}", "author": b["name"], "keywords": "goods receipt",
                      "creationDate": pdf_date(gr["date"])}

    # ================================================================== invoice (supplier)
    def invoice(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        view = doc_view(m)
        t = view["invoice_totals"]
        inv = d["invoice"]
        pt = m["msa_terms"]["payment_terms"]
        rows = "".join(
            f"<tr><td class='c'>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td>"
            f"<td class='r'>{de_num(li['quantity'], 0)}</td><td class='c'>{li['unit']}</td>"
            f"<td class='r'>{de_num(li['unit_price'])}</td><td class='r'>{de_num(li['line_total'])}</td></tr>"
            for li in view["invoice"]
        )
        step = m["line_items"][1]["position"] - m["line_items"][0]["position"]
        rows += "".join(
            f"<tr><td class='c'>{m['line_items'][-1]['position'] + step * (k + 1)}</td><td class='ino'></td><td>{esc(sc['label'])}</td>"
            f"<td class='r'>1</td><td class='c'>LS</td><td class='r'>{de_num(sc['amount'])}</td><td class='r'>{de_num(sc['amount'])}</td></tr>"
            for k, sc in enumerate(view["invoice_surcharges"])
        )
        grid = self._ref_grid([
            ("Invoice no.", inv["number"]), ("Invoice date", de_date(inv["date"])),
            ("Customer PO", d["purchase_order"]["number"]), ("Delivery note", d["delivery_note"]["number"]),
            ("Framework agr.", d["msa"]["number"]), ("Date of supply", de_date(d["delivery_note"]["date"])),
            ("Customer no.", s["customer_number_for_buyer"]), ("Customer VAT ID", b["vat_id"]),
        ])
        html = f"""
        {self._supplier_logo('INVOICE')}
        <div style='height:10px'></div>
        <table style='width:100%'><tr>
          <td width='50%' style='vertical-align:top'><div class='lbl'>Bill to</div>
            <div class='addr'>{esc(b['name'])}<br/>Accounts Payable<br/>{b['address']['street']}<br/>{b['address']['postal_code']} {b['address']['city']}</div></td>
          <td width='50%' style='vertical-align:top;font-size:8pt;line-height:1.5'>Your contact: {s['contact']['name']}<br/>{s['contact']['phone']}<br/>{s['contact']['email']}<br/>Our VAT ID: {s['vat_id']}</td>
        </tr></table>
        <div style='height:10px'></div>
        {grid}
        <p style='margin-top:12px'>We invoice the following deliveries under framework agreement {d['msa']['number']}:</p>
        <table class='items'>
          <tr><th class='c'>Pos.</th><th>Item no.</th><th>Description</th><th class='r'>Qty</th><th class='c'>UoM</th><th class='r'>Unit price</th><th class='r'>Amount</th></tr>
          {rows}
        </table>
        <table style='width:100%;margin-top:8px'><tr><td width='48%'></td><td width='52%'>
          <table class='tot'>
            <tr><td>Net amount</td><td class='r'>{money(t['net_total'])}</td></tr>
            <tr><td>VAT {de_num(t['vat_rate_percent'], 0)} %</td><td class='r'>{money(t['vat_amount'])}</td></tr>
            <tr class='g'><td>Amount due</td><td class='r'>{money(t['gross_total'])}</td></tr>
          </table></td></tr></table>
        <div class='pay'>
          <b>Terms of payment:</b> {pt['net_days']} days net – due on {de_date(inv['due_date'])}.<br/>
          Early-payment discount: {de_num(pt['early_payment_discount_percent'], 0)} % ({money(t['early_payment_discount_amount'])}) if payment is received
          by {de_date(inv['discount_deadline'])} ({pt['discount_days']} days); discounted amount {money(t['amount_payable_within_discount_period'])}.<br/>
          Bank: {s['bank']['bank_name']} · IBAN {iban_grouped(s['bank']['iban'])} · BIC {s['bank']['bic']} · Reference: {inv['number']}
        </div>
        <p style='font-size:7.6pt;color:#607d8b;margin-top:8px'>Unit prices per Annex 1 of framework agreement {d['msa']['number']} (price lock until
        {de_date(m['msa_terms']['price_lock']['end_date'])}). Tax no. {s['tax_number']}. Goods remain subject to export control regulations.</p>
        """
        spec = RenderSpec([html], self._supplier_css(), top=40, bottom=80, left=44, right=40,
                          decor=PageDecor(header=self._supplier_header, footer=self._supplier_footer()))
        return spec, {"title": f"Invoice {inv['number']}", "author": s["name"], "keywords": "invoice",
                      "creationDate": pdf_date(inv["date"])}

    # ================================================================== MSA
    def msa(self, toc_pages: dict[int, int] | None = None):
        m, b, s, d = self.m, self.b, self.s, self.d
        mt = m["msa_terms"]
        pt = mt["payment_terms"]
        clauses = build_clauses("electronics")
        num = lambda prefix: clause_index(clauses, prefix)  # noqa: E731
        ctx = {
            "goods": "electronic components (in particular passive components, semiconductors, electromechanical components and frequency control devices)",
            "approval_dept": "Strategic Procurement department",
            "c_ordering": f"§ {num('Ordering Process')}",
            "c_delivery_dates": f"§ {num('Delivery Dates')}",
            "c_prices": f"§ {num('Prices and Price List')}",
            "forecast_months": "nine", "confirm_days": "two", "cancel_days": "ten",
            "lock_months": mt["price_lock"]["months"], "lock_end": de_date(mt["price_lock"]["end_date"]),
            "incoterm": mt["incoterm"],
            "delivery_place": f"{b['warehouse']['street']}, {b['warehouse']['postal_code']} {b['warehouse']['city']}",
            "receiving_hours": b["warehouse"]["receiving_hours"],
            "lead_time": mt["lead_time_business_days"],
            "penalty_rate": mt["late_delivery_penalty"]["rate_text"],
            "penalty_unit": mt["late_delivery_penalty"]["per"],
            "penalty_cap": mt["late_delivery_penalty"]["cap_text"],
            "warranty_months": mt["warranty_months"],
            "invoice_email": b["accounts_payable"]["email"],
            "net_days": pt["net_days"], "disc_days": pt["discount_days"],
            "disc_pct": de_num(pt["early_payment_discount_percent"], 0),
            "safety_weeks": "six", "insurance": "EUR 10,000,000", "liability_cap": "EUR 2,500,000",
            "conf_years": "three", "effective_date": de_date(d["msa"]["effective_date"]),
            "term_years": mt["initial_term"], "notice": mt["termination_notice"], "court": "Cologne",
        }
        summaries = {
            "price_lock": f"Prices fixed for {mt['price_lock']['months']} months until {mt['price_lock']['end_date']}",
            "surcharge": "No surcharges of any kind (incl. fuel/energy) unless pre-approved in writing by Buyer's Purchasing (Strategic Procurement) department",
            "payment_terms": f"{pt['net_days']} days net; {pt['early_payment_discount_percent']} % discount within {pt['discount_days']} days",
            "penalty": f"{mt['late_delivery_penalty']['rate_text']} per commenced Business Day, max {mt['late_delivery_penalty']['cap_text']} of delayed net order value",
        }
        key_clauses, blocks = {}, []
        for ci, c in enumerate(clauses, start=1):
            head = f"<div class='ph'>§ {ci}</div><div class='pt'>{esc(c['title'])}</div>"
            parts = []
            for pi, para in enumerate(c["paras"], start=1):
                if isinstance(para, str):
                    para = {"text": para}
                text = para["text"].format(**ctx)
                lbl = f"({pi})" if len(c["paras"]) > 1 else ""
                inner = f"<p class='sc'>{lbl + '&nbsp;' if lbl else ''}{text}</p>"
                if "items" in para:
                    inner += "".join(f"<p class='li'>{chr(97 + k)})&nbsp;{it.format(**ctx)}</p>" for k, it in enumerate(para["items"]))
                parts.append(inner)
                if para.get("key"):
                    key_clauses[para["key"]] = {
                        "clause": f"§ {ci} ({pi})", "clause_title": f"§ {ci} {c['title']}", "search_label": lbl,
                        "opening": " ".join(text.split()[:9]), "summary": summaries[para["key"]],
                    }
            blocks.append((head + "".join(parts), head + parts[0][: parts[0].find("</p>") + 4]))

        cover = f"""
        <div style='height:70px'></div>
        <p class='cv1'>FRAMEWORK SUPPLY AGREEMENT</p>
        <p class='cv2'>(Master Supply Agreement) for Electronic Components</p>
        <p class='cv3'>Contract No. {d['msa']['number']}</p>
        <div style='height:40px'></div>
        <table class='cvp'><tr>
          <td style='width:215px'><b>{esc(b['name'])}</b><br/>{b['address']['street']}<br/>{b['address']['postal_code']} {b['address']['city']}<br/>{b['registration']['court']}<br/>{b['registration']['number']}<br/>VAT ID {b['vat_id']}<br/><br/><i>– the “Buyer” –</i></td>
          <td style='width:33px;text-align:center'>&amp;</td>
          <td style='width:215px'><b>{esc(s['name'])}</b><br/>{s['address']['street']}<br/>{s['address']['postal_code']} {s['address']['city']}<br/>{s['registration']['court']}<br/>{s['registration']['number']}<br/>VAT ID {s['vat_id']}<br/><br/><i>– the “Supplier” –</i></td>
        </tr></table>
        <div style='height:40px'></div>
        <p class='cv4'>Effective Date: {de_date(d['msa']['effective_date'])} &nbsp;·&nbsp; Signed: {de_date(d['msa']['signing_date'])}</p>
        <p class='cv4'>Confidential – for internal use of the Parties only</p>
        """
        toc_rows = "".join(
            f"<tr><td width='9%'>§ {ci}</td><td>{esc(c['title'])}</td><td width='8%' class='r'>{(toc_pages or {}).get(ci, 0):>2}</td></tr>"
            for ci, c in enumerate(clauses, start=1)
        )
        toc = f"""<p class='toch'>Contents</p><table class='toc'>{toc_rows}
            <tr><td></td><td>Signatures</td><td class='r'>{(toc_pages or {}).get(0, 0)}</td></tr>
            <tr><td></td><td>Annex 1 – Price List; Annex 2 – Contacts and Bank Details; Annex 3 – Supplier Evaluation</td><td class='r'>{(toc_pages or {}).get(-1, 0)}</td></tr></table>"""
        preamble = f"""
        <div class='ph'>Preamble</div>
        <p class='sc'>The Buyer develops and manufactures electronic assemblies and control units for industrial customers at its
        plant in {b['address']['city']}. The Supplier is an authorised distributor of electronic components with a central warehouse in
        {s['address']['city']}. Following the Buyer’s supplier qualification in 2025, the Parties wish to set out the terms on which the
        Supplier supplies electronic components to the Buyer and therefore agree as follows:</p>
        """
        sig = f"""
        <div class='ph'>Signatures</div>
        <table class='sig'><tr>
          <td width='46%'>Köln, {de_date(d['msa']['signing_date'])}<br/><b>{esc(b['name'])}</b><br/><br/><br/><br/>
          <div class='line'>{b['managing_directors'][0]}, Managing Director (CEO)</div><br/><br/><br/>
          <div class='line'>{b['managing_directors'][1]}, Managing Director (CFO)</div></td>
          <td width='8%'></td>
          <td width='46%'>Frankfurt am Main, {de_date(d['msa']['signing_date'])}<br/><b>{esc(s['name'])}</b><br/><br/><br/><br/>
          <div class='line'>{s['managing_directors'][0]}, Managing Director</div><br/><br/><br/>
          <div class='line'>{s['contact']['name']}, Authorised Signatory (Prokurist)</div></td>
        </tr></table>
        """
        pl_rows = "".join(
            f"<tr class='{'z' if i % 2 else ''}'><td class='ino'>{p['item_no']}</td><td>{esc(p['description'])}</td><td class='c'>{p['unit']}</td><td class='r'>{de_num(p['unit_price'])}</td></tr>"
            for i, p in enumerate(m["price_list"])
        )
        annex1 = f"""
        <div class='ph'>Annex 1</div><div class='pt'>Price List</div>
        <p class='sc'>Framework Supply Agreement No. {d['msa']['number']}. All prices in EUR per unit of measure (UoM), net, excluding
        statutory VAT, {mt['incoterm']} Köln (Incoterms® 2020), including ESD/MSL-compliant packaging, freight and certificates of conformance.
        The prices are fixed from {de_date(mt['price_lock']['start_date'])} to {de_date(mt['price_lock']['end_date'])}.</p>
        <table class='pl'><tr><th>Item no.</th><th>Description</th><th class='c'>UoM</th><th class='r'>Price EUR</th></tr>{pl_rows}</table>
        <p class='sc' style='font-size:8.5pt'>Reels are supplied as full reels only. Minimum order quantity per item: one reel or 100 pieces.
        Lead time: {mt['lead_time_business_days']} Business Days from Order for stock items.</p>
        """
        kpi_rows = "".join(f"<tr><td><b>{k}</b></td><td>{dfn}</td><td class='c'>{tgt}</td><td>{mm}</td></tr>" for k, dfn, tgt, mm in annex_kpis())
        esc_rows = "".join(f"<tr><td><b>{lv}</b></td><td>{bb}</td><td>{ss}</td><td class='c'>{rt}</td></tr>" for lv, bb, ss, rt in escalation(b, s))
        annex23 = f"""
        <div class='ph'>Annex 2</div><div class='pt'>Delivery Address, Contact Persons and Bank Details</div>
        <table class='pl'>
          <tr><th width='22%'></th><th width='39%'>Buyer</th><th width='39%'>Supplier</th></tr>
          <tr><td>Delivery Address / Shipping point</td><td>{b['warehouse']['name']}, {b['warehouse']['street']}, {b['warehouse']['postal_code']} {b['warehouse']['city']}</td><td>{s['address']['street']}, {s['address']['postal_code']} {s['address']['city']}</td></tr>
          <tr><td>Commercial contact</td><td>{b['contact']['name']}<br/>{b['contact']['phone']}<br/>{b['contact']['email']}</td><td>{s['contact']['name']}<br/>{s['contact']['phone']}<br/>{s['contact']['email']}</td></tr>
          <tr><td>Invoices</td><td>{b['accounts_payable']['name']}, {b['accounts_payable']['email']}</td><td>{s['email']}</td></tr>
          <tr><td>Bank account</td><td>{b['bank']['bank_name']}<br/>IBAN {iban_grouped(b['bank']['iban'])}</td><td>{s['bank']['bank_name']}<br/>IBAN {iban_grouped(s['bank']['iban'])}<br/>BIC {s['bank']['bic']}</td></tr>
        </table>
        <div style='height:10px'></div>
        <div class='ph'>Annex 3</div><div class='pt'>Supplier Evaluation and Escalation</div>
        <table class='pl'><tr><th width='18%'>Key figure</th><th width='40%'>Definition</th><th width='14%' class='c'>Target</th><th width='28%'>Measurement</th></tr>{kpi_rows}</table>
        <table class='pl'><tr><th width='22%'>Level</th><th width='31%'>Buyer</th><th width='31%'>Supplier</th><th width='16%' class='c'>Response time</th></tr>{esc_rows}</table>
        """
        css = f"""
        body {{font-family:serif;font-size:9.6pt;color:#222;line-height:1.42}}
        div.ph {{text-align:center;font-weight:bold;font-size:10.5pt;color:{WINE};margin-top:12px}}
        div.pt {{text-align:center;font-weight:bold;font-size:10pt;margin-bottom:6px}}
        p.sc {{margin:0 0 5px 0;text-align:justify}}
        p.li {{margin:0 0 3px 26px;text-align:justify}}
        p.cv1 {{text-align:center;font-size:22pt;color:{WINE};letter-spacing:2px;margin:0}}
        p.cv2 {{text-align:center;font-size:12pt;font-style:italic;margin:4px 0}}
        p.cv3 {{text-align:center;font-size:10.5pt;margin:12px 0}}
        p.cv4 {{text-align:center;font-size:9pt;color:#6b5a60}}
        table.cvp {{width:100%;font-size:10pt;line-height:1.5}} table.cvp td {{vertical-align:top}}
        p.toch {{font-size:14pt;color:{WINE};margin:0 0 8px 0}}
        table.toc {{width:100%;font-size:9pt;border-collapse:collapse}} table.toc td {{padding:1.6px 2px;border-bottom:0.3px dotted #b9a4ac}}
        table.sig {{width:100%;margin-top:16px}} table.sig td {{vertical-align:top}}
        div.line {{border-top:0.7px solid #333;padding-top:2px;font-size:8.6pt}}
        table.pl {{width:100%;border-collapse:collapse;font-size:8.4pt;margin:6px 0 10px 0}}
        table.pl th {{color:{WINE};text-align:left;padding:4px 3px;border-top:0.8px solid {WINE};border-bottom:2.2px double {WINE}}}
        table.pl td {{padding:4px 3px;vertical-align:top;border-bottom:0.3px solid #d8c9cf}}
        tr.z td {{background-color:{WINE_LIGHT}}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} .c {{text-align:center}} table.pl th.r {{text-align:right}} table.pl th.c {{text-align:center}}
        """

        def header(page, n, total):
            if n == 1:
                return
            htmlbox(page, (60, 24, page.rect.width - 60, 42),
                    f"<div style='font-family:serif;font-size:7.5pt;font-style:italic;color:#6b5a60;text-align:right;border-bottom:0.4px solid #a07a3f'>"
                    f"Framework Supply Agreement No. {d['msa']['number']} – {esc(b['short_name'])} / {esc(s['short_name'])}</div>")

        def footer(page, n, total):
            htmlbox(page, (60, page.rect.height - 46, page.rect.width - 60, page.rect.height - 24),
                    "<table style='width:100%;font-family:serif;font-size:7.5pt;color:#6b5a60'><tr>"
                    "<td width='40%'>Initials: Buyer ______ Supplier ______</td>"
                    f"<td width='20%' style='text-align:center'>– {n} of {total} –</td><td width='40%'></td></tr></table>")

        spec = RenderSpec([cover, toc, [preamble] + blocks + [(sig, sig)], annex1, annex23], css,
                          top=58, bottom=58, left=66, right=66, decor=PageDecor(header=header, footer=footer))
        meta = {"title": f"Framework Supply Agreement {d['msa']['number']}", "author": f"{b['name']} / {s['name']}",
                "keywords": "master supply agreement, framework supply agreement, MSA", "creationDate": pdf_date(d["msa"]["signing_date"])}
        return spec, meta, key_clauses

    def msa_toc(self, pdf_path) -> dict[int, int]:
        """Read the real start page of every § heading from a rendered MSA (for the table of contents)."""
        doc = pymupdf.open(str(pdf_path))
        pages: dict[int, int] = {}
        for pno in range(2, doc.page_count):  # skip cover + contents
            lines = [ln.strip() for ln in doc[pno].get_text().splitlines()]
            for ln in lines:
                mt = re.fullmatch(r"§ (\d+)", ln)
                if mt:
                    pages.setdefault(int(mt.group(1)), pno + 1)
                if ln == "Signatures":
                    pages.setdefault(0, pno + 1)
                if ln == "Annex 1":
                    pages.setdefault(-1, pno + 1)
        doc.close()
        return pages

    # ================================================================== guideline
    def purchasing_guideline(self):
        b = self.b
        g = self.m["guideline"]
        secs = guideline_sections({**g, "buyer_name": esc(b["name"])})
        blocks = [(f"<h2>{i}. {t}</h2>{h}",) * 2 for i, (t, h) in enumerate(secs, start=1)]
        top = f"""
        <table><tr>
          <td style='width:275px'><p class='k'>INTERNAL POLICY · STRATEGIC PROCUREMENT</p>
          <h1>Purchasing and Invoice Approval Policy</h1></td>
          <td style='width:200px;vertical-align:top'>
            <table class='dc'>
              <tr><td style='width:58px'>Policy no.</td><td style='width:128px'>{g['number']}</td></tr>
              <tr><td>Version</td><td>{g['version']}</td></tr>
              <tr><td>In force since</td><td>{de_date(g['valid_from'])}</td></tr>
              <tr><td>Owner</td><td>{g['owner']}</td></tr>
            </table></td></tr></table>
        <p class='appr'>Approved by: {g['approved_by']}</p>
        """
        css = f"""
        body {{font-family:serif;font-size:9.4pt;color:#2b2326;line-height:1.42}}
        h1 {{font-size:16pt;color:{WINE};margin:2px 0 4px 0;font-weight:normal}}
        h2 {{font-size:10.5pt;color:{WINE};margin:12px 0 4px 0;border-bottom:0.6px solid {GOLD};padding-bottom:1px}}
        p {{margin:0 0 6px 0;text-align:justify}}
        p.k {{font-size:7.5pt;color:{GOLD};letter-spacing:1px;margin:0}}
        p.appr {{font-size:8pt;font-style:italic;color:#6b5a60;border-bottom:0.6px solid {GOLD};padding-bottom:4px}}
        ol {{margin:2px 0 6px 0}}
        table.dc {{width:100%;font-size:7.8pt;border-collapse:collapse}} table.dc td {{padding:1.5px 3px;border-bottom:0.4px dotted #c9b3bb}}
        table.tbl {{width:100%;border-collapse:collapse;font-size:8.3pt;margin:4px 0 8px 0}}
        table.tbl th {{color:{WINE};text-align:left;padding:3px;border-top:0.8px solid {WINE};border-bottom:2.2px double {WINE}}}
        table.tbl td {{padding:3px;vertical-align:top;border-bottom:0.3px solid #d8c9cf}}
        div.note {{border:0.8px solid {WINE};background-color:{WINE_LIGHT};padding:6px 8px;font-size:8.6pt;margin:4px 0 8px 0;font-style:italic}}
        """
        spec = RenderSpec([[top] + blocks], css, top=86, bottom=74, left=56, right=56,
                          decor=PageDecor(header=self._buyer_band("Internal Policy"), footer=self._buyer_footer(f"{g['number']} v{g['version']} · ")))
        return spec, {"title": f"Purchasing Policy {g['number']}", "author": b["name"], "keywords": "purchasing guideline",
                      "creationDate": pdf_date(g["valid_from"])}
