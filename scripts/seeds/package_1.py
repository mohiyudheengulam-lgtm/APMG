"""Seed package 1: Lorvaten Fördertechnik GmbH (buyer) <- Pakvero Industriebedarf GmbH (supplier).

Packaging materials and fasteners. Sans-serif, navy (buyer) / green (supplier) corporate design,
DIN-5008-style letter layout, decimal clause numbering (7.3).
All companies, people, addresses, VAT IDs, IBANs and phone numbers are fictional
(phone numbers use the Bundesnetzagentur ranges reserved for fictional use).
"""

from __future__ import annotations

from datetime import date, timedelta

import pymupdf

from common import (
    PageDecor, RenderSpec, de_date, de_num, doc_view, esc, htmlbox, iban_checksum, iban_grouped, pdf_date,
)
from guideline_text import guideline_sections
from msa_clauses import annex_kpis, build_clauses, clause_index, escalation


def _add_days(iso: str, n: int) -> str:
    return (date.fromisoformat(iso) + timedelta(days=n)).isoformat()


MSA_EFFECTIVE = "2026-01-15"
INVOICE_DATE = "2026-09-18"
NET_DAYS, DISC_DAYS = 30, 14

CONFIG = {
    "package_name": "seed_01_packaging_fasteners",
    "description": "Clean package: packaging materials and fasteners, all documents consistent.",
    "currency": "EUR",
    "vat_rate": "19",
    "buyer": {
        "name": "Lorvaten Fördertechnik GmbH",
        "short_name": "Lorvaten",
        "address": {"street": "Brunnthaler Ring 18", "postal_code": "81829", "city": "München", "country": "Germany"},
        "vat_id": "DE318274905",
        "registration": {"court": "Amtsgericht München", "number": "HRB 241873"},
        "managing_directors": ["Dr. Katrin Wendeborn", "Thomas Ahlgrimm"],
        "phone": "+49 89 99998-200",
        "email": "einkauf@lorvaten-foerdertechnik.de",
        "website": "www.lorvaten-foerdertechnik.de",
        "contact": {"name": "Sabine Hofreiter", "role": "Senior Buyer, Purchasing Department",
                    "phone": "+49 89 99998-214", "email": "s.hofreiter@lorvaten-foerdertechnik.de"},
        "accounts_payable": {"name": "Petra Leitner", "email": "kreditoren@lorvaten-foerdertechnik.de"},
        "bank": {"bank_name": "Isartal Handelsbank AG", "iban": iban_checksum("DE", "70051899" + "0441726031"), "bic": "ISHBDEM1XXX"},
        "warehouse": {"name": "Central Warehouse, Gate 3", "street": "Brunnthaler Ring 22", "postal_code": "81829",
                      "city": "München", "receiving_hours": "07:00 and 15:00"},
        "supplier_number_for_supplier": "K-70418",
    },
    "supplier": {
        "name": "Pakvero Industriebedarf GmbH",
        "short_name": "Pakvero",
        "address": {"street": "Am Hafenbogen 41", "postal_code": "21129", "city": "Hamburg", "country": "Germany"},
        "vat_id": "DE294117638",
        "tax_number": "47/712/03518",
        "registration": {"court": "Amtsgericht Hamburg", "number": "HRB 158337"},
        "managing_directors": ["Henrik Matthiesen", "Lena Carstensen"],
        "phone": "+49 40 66969-310",
        "email": "vertrieb@pakvero-industriebedarf.de",
        "website": "www.pakvero-industriebedarf.de",
        "contact": {"name": "Ole Petersen", "role": "Key Account Manager",
                    "phone": "+49 40 66969-342", "email": "o.petersen@pakvero-industriebedarf.de"},
        "dispatch_contact": "Kai Wolters",
        "bank": {"bank_name": "Hanseatische Gewerbebank AG", "iban": iban_checksum("DE", "2006943107" + "38815200"), "bic": "HGWBDEHHXXX"},
        "customer_number_for_buyer": "40-11873",
    },
    "documents": {
        "msa": {"number": "MSA-LFT-PKV-2026-01", "signing_date": "2026-01-12", "effective_date": MSA_EFFECTIVE},
        "purchase_order": {"number": "PO-2026-004817", "date": "2026-09-08", "requested_delivery_date": "2026-09-18"},
        "delivery_note": {"number": "LS-26-09-3321", "date": "2026-09-17", "packages": "3 pallets",
                          "gross_weight_kg": "684"},
        "goods_receipt": {"number": "WE-2026-01562", "date": "2026-09-17", "receiving_clerk": "Jonas Brüggemann",
                          "storage_location": "ZL-A"},
        "invoice": {"number": "RE-2026-10457", "date": INVOICE_DATE,
                    "due_date": _add_days(INVOICE_DATE, NET_DAYS),
                    "discount_deadline": _add_days(INVOICE_DATE, DISC_DAYS)},
    },
    "msa_terms": {
        "payment_terms": {"net_days": NET_DAYS, "early_payment_discount_percent": "2", "discount_days": DISC_DAYS,
                          "discount_base": "gross invoice amount"},
        "price_lock": {"months": 12, "start_date": MSA_EFFECTIVE, "end_date": "2027-01-14"},
        "surcharge_rule": "Surcharges of any kind (incl. fuel/energy surcharges) are not permitted unless approved "
                          "in advance and in writing by the Buyer's Purchasing Department for the specific order.",
        "late_delivery_penalty": {"rate_percent": "0.5", "per": "each commenced calendar day",
                                  "cap_percent": "5", "basis": "net order value of the delayed goods",
                                  "rate_text": "0.5 %", "cap_text": "5 %"},
        "incoterm": "DAP",
        "lead_time_business_days": 7,
        "warranty_months": 24,
        "governing_law": "Germany (CISG excluded)",
        "jurisdiction": "Munich",
        "initial_term": "three (3) years",
        "termination_notice": "six (6) months’",
    },
    "price_list": [
        {"item_no": "PV-KS-4030", "description": "Corrugated shipping carton, double wall BC flute, 400 x 300 x 300 mm", "unit": "pcs", "unit_price": "1.38"},
        {"item_no": "PV-KS-6040", "description": "Corrugated shipping carton, double wall BC flute, 600 x 400 x 400 mm", "unit": "pcs", "unit_price": "2.46"},
        {"item_no": "PV-SF-500", "description": "Machine stretch film 500 mm x 1,500 m, 23 µm, transparent", "unit": "roll", "unit_price": "14.90"},
        {"item_no": "PV-KB-50", "description": "PP packaging tape 50 mm x 66 m, brown, low-noise", "unit": "roll", "unit_price": "1.65"},
        {"item_no": "PV-KS-35", "description": "PE edge protector 35 x 35 x 3 mm, length 1,200 mm", "unit": "pcs", "unit_price": "0.42"},
        {"item_no": "PV-LB-1015", "description": "Thermal transfer labels 100 x 150 mm, 500 per roll", "unit": "roll", "unit_price": "6.80"},
        {"item_no": "BF-SK-M8x30", "description": "Hex head screw DIN 933 M8 x 30, 8.8, zinc plated (box of 200)", "unit": "box", "unit_price": "18.40"},
        {"item_no": "BF-SK-M10x40", "description": "Hex head screw DIN 933 M10 x 40, 8.8, zinc plated (box of 100)", "unit": "box", "unit_price": "23.90"},
        {"item_no": "BF-MU-M8", "description": "Hex nut DIN 934 M8, class 8, zinc plated (box of 500)", "unit": "box", "unit_price": "12.75"},
        {"item_no": "BF-US-8.4", "description": "Flat washer DIN 125-A 8.4, steel, zinc plated (box of 1,000)", "unit": "box", "unit_price": "9.80"},
    ],
    "order_items": [
        {"item_no": "PV-KS-4030", "description": "Corrugated shipping carton, double wall BC flute, 400 x 300 x 300 mm", "unit": "pcs", "quantity": 1200, "unit_price": "1.38"},
        {"item_no": "PV-SF-500", "description": "Machine stretch film 500 mm x 1,500 m, 23 µm, transparent", "unit": "roll", "quantity": 48, "unit_price": "14.90"},
        {"item_no": "PV-KB-50", "description": "PP packaging tape 50 mm x 66 m, brown, low-noise", "unit": "roll", "quantity": 240, "unit_price": "1.65"},
        {"item_no": "PV-KS-35", "description": "PE edge protector 35 x 35 x 3 mm, length 1,200 mm", "unit": "pcs", "quantity": 600, "unit_price": "0.42"},
        {"item_no": "BF-SK-M8x30", "description": "Hex head screw DIN 933 M8 x 30, 8.8, zinc plated (box of 200)", "unit": "box", "quantity": 25, "unit_price": "18.40"},
        {"item_no": "BF-MU-M8", "description": "Hex nut DIN 934 M8, class 8, zinc plated (box of 500)", "unit": "box", "quantity": 10, "unit_price": "12.75"},
        {"item_no": "BF-US-8.4", "description": "Flat washer DIN 125-A 8.4, steel, zinc plated (box of 1,000)", "unit": "box", "quantity": 8, "unit_price": "9.80"},
    ],
    "guideline": {
        "number": "EK-RL-04", "version": "3.2", "valid_from": "2026-01-01", "owner": "Head of Purchasing",
        "approved_by": "Dr. Katrin Wendeborn, Managing Director", "payment_runs": "every Tuesday and Friday",
        "thresholds": [
            {"range": "up to 5,000.00", "approver": "Purchaser / budget owner of the cost centre", "form": "ERP workflow, single approval"},
            {"range": "5,000.01 – 25,000.00", "approver": "Head of Purchasing", "form": "ERP workflow, second approval"},
            {"range": "25,000.01 – 100,000.00", "approver": "Head of Purchasing and Commercial Director", "form": "ERP workflow, dual approval"},
            {"range": "above 100,000.00", "approver": "Managing Director", "form": "ERP workflow + signed approval memo"},
        ],
        "roles": [
            ("Purchasing Department", "Issues purchase orders, maintains MSA price lists in the ERP system, approves surcharges in writing where justified, resolves price discrepancies with suppliers."),
            ("Central Warehouse", "Checks deliveries against the delivery note, posts the goods receipt with the quantities actually received on the day of delivery, records damage and shortfalls."),
            ("Accounts Payable", "Records incoming invoices, performs the three-way match and the arithmetic check, blocks invoices with discrepancies and routes them to the responsible approver."),
            ("Budget owner / approver", "Approves invoices within the thresholds in section 2 after a successful three-way match."),
            ("Head of Purchasing", "Decides on escalated discrepancies and on exceptions to this guideline; exceptions must be documented in writing."),
        ],
    },
}

NAVY, NAVY_LIGHT, GREY = "#1f3a5f", "#e8eef5", "#5b6470"
GREEN, GREEN_LIGHT = "#2f6b3a", "#eef5ef"


def addr_lines(p: dict) -> str:
    a = p["address"]
    return f"{esc(p['name'])}<br/>{a['street']}<br/>{a['postal_code']} {a['city']}"


class Layout:
    def __init__(self, m: dict):
        self.m = m
        self.b, self.s, self.d = m["buyer"], m["supplier"], m["documents"]
        self.t = m["totals"]

    # ------------------------------------------------------------------ formatting
    @staticmethod
    def money(v) -> str:
        return f"{de_num(v)} €"

    # ------------------------------------------------------------------ footers
    def _buyer_footer(self, internal: str | None = None):
        b = self.b

        def footer(page: pymupdf.Page, n: int, total: int):
            r = page.rect
            page.draw_line((56, r.height - 78), (r.width - 56, r.height - 78), color=(0.12, 0.23, 0.37), width=0.8)
            mds = ", ".join(b["managing_directors"])
            html = (
                "<table style='width:100%;font-family:sans-serif;font-size:6.5pt;color:#5b6470;line-height:1.35'><tr>"
                f"<td style='width:27%;vertical-align:top'><b style='color:{NAVY}'>{esc(b['name'])}</b><br/>{b['address']['street']}<br/>{b['address']['postal_code']} {b['address']['city']}, Germany</td>"
                f"<td style='width:25%;vertical-align:top'>Registered office: München<br/>{b['registration']['court']}, {b['registration']['number']}<br/>Managing Directors: {mds}</td>"
                f"<td style='width:22%;vertical-align:top'>Phone {b['phone']}<br/>{b['email']}<br/>{b['website']}<br/>VAT ID {b['vat_id']}</td>"
                f"<td style='width:26%;vertical-align:top'>{b['bank']['bank_name']}<br/>IBAN {iban_grouped(b['bank']['iban'])}<br/>BIC {b['bank']['bic']}</td>"
                "</tr></table>"
            )
            htmlbox(page, (56, r.height - 74, r.width - 56, r.height - 22), html)
            right = f"Page {n} of {total}" + (f" · {internal}" if internal else "")
            htmlbox(page, (56, r.height - 24, r.width - 56, r.height - 12),
                    f"<div style='text-align:right;font-family:sans-serif;font-size:6.5pt;color:#5b6470'>{right}</div>")

        return footer

    def _supplier_footer(self):
        s = self.s

        def footer(page: pymupdf.Page, n: int, total: int):
            r = page.rect
            band = pymupdf.Rect(0, r.height - 70, r.width, r.height)
            page.draw_rect(band, color=None, fill=(0.94, 0.95, 0.94))
            page.draw_rect(pymupdf.Rect(0, r.height - 71, r.width, r.height - 69), color=None, fill=(0.18, 0.42, 0.23))
            mds = " · ".join(s["managing_directors"])
            html = (
                "<table style='width:100%;font-family:sans-serif;font-size:6.6pt;color:#3a3f45;line-height:1.4'><tr>"
                f"<td style='width:34%;vertical-align:top'><b>{esc(s['name'])}</b><br/>{s['address']['street']} · {s['address']['postal_code']} {s['address']['city']}<br/>"
                f"Tel. {s['phone']}<br/>{s['email']}</td>"
                f"<td style='width:33%;vertical-align:top'>Court of registration: {s['registration']['court']}<br/>{s['registration']['number']} · VAT ID {s['vat_id']}<br/>Managing Directors: {mds}</td>"
                f"<td style='width:33%;vertical-align:top'>Bank: {s['bank']['bank_name']}<br/>IBAN {iban_grouped(s['bank']['iban'])}<br/>BIC {s['bank']['bic']}</td>"
                "</tr></table>"
            )
            htmlbox(page, (40, r.height - 62, r.width - 40, r.height - 14), html)
            if total > 1:
                htmlbox(page, (r.width - 140, r.height - 92, r.width - 40, r.height - 78),
                        f"<div style='text-align:right;font-family:sans-serif;font-size:7pt;color:#5b6470'>Page {n}/{total}</div>")

        return footer

    @staticmethod
    def _supplier_header(page: pymupdf.Page, n: int, total: int):
        page.draw_rect(pymupdf.Rect(0, 0, page.rect.width, 7), color=None, fill=(0.18, 0.42, 0.23))

    # ------------------------------------------------------------------ building blocks
    def _buyer_logo(self, title: str, subtitle: str = "") -> str:
        return (
            "<table style='width:100%'><tr>"
            f"<td style='width:30px;background-color:{NAVY};color:white;font-size:15pt;font-weight:bold;text-align:center;padding:6px 4px'>LF</td>"
            f"<td style='padding-left:8px;vertical-align:middle'><span style='font-size:15pt;font-weight:bold;color:{NAVY}'>LORVATEN</span><br/>"
            f"<span style='font-size:7.5pt;color:{GREY}'>Fördertechnik GmbH · Conveyor Systems</span></td>"
            f"<td style='text-align:right;vertical-align:bottom'><span style='font-size:17pt;font-weight:bold;color:{NAVY}'>{title}</span>"
            + (f"<br/><span style='font-size:8pt;color:{GREY}'>{subtitle}</span>" if subtitle else "")
            + "</td></tr></table>"
        )

    def _supplier_logo(self) -> str:
        return (
            "<table style='width:100%'><tr><td></td>"
            f"<td style='text-align:right'><span style='font-size:22pt;font-weight:bold;color:{GREEN}'>pakvero</span><br/>"
            f"<span style='font-size:7pt;color:{GREY}'>INDUSTRIEBEDARF · PACKAGING · FASTENERS</span></td></tr></table>"
        )

    def _sender_line(self, p: dict) -> str:
        a = p["address"]
        return (f"<div style='font-size:6.5pt;color:{GREY};border-bottom:0.5px solid #9aa1a8;padding-bottom:1px;margin-bottom:4px'>"
                f"{esc(p['name'])} · {a['street']} · {a['postal_code']} {a['city']}</div>")

    def _info_table(self, rows: list[tuple[str, str]], color: str) -> str:
        cells = "".join(
            f"<tr><td style='color:{GREY};padding:1px 6px 1px 0'>{k}</td><td style='padding:1px 0;font-weight:bold;color:#222'>{v}</td></tr>"
            for k, v in rows
        )
        return f"<table style='font-size:8pt;border-left:2px solid {color};padding-left:6px'>{cells}</table>"

    # ------------------------------------------------------------------ purchase order
    def purchase_order(self):
        m, b, s, d, t = self.m, self.b, self.s, self.d, self.t
        po = d["purchase_order"]
        w = b["warehouse"]
        info = self._info_table([
            ("PO number", po["number"]), ("PO date", de_date(po["date"])),
            ("Framework agreement", d["msa"]["number"]), ("Supplier no.", b["supplier_number_for_supplier"]),
            ("Buyer", b["contact"]["name"]), ("Phone", b["contact"]["phone"]), ("E-mail", b["contact"]["email"]),
        ], NAVY)
        rows = ""
        for i, li in enumerate(m["line_items"]):
            bg = NAVY_LIGHT if i % 2 else "white"
            rows += (
                f"<tr style='background-color:{bg}'>"
                f"<td class='c'>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td>"
                f"<td class='c'>{li['unit']}</td><td class='r'>{de_num(li['quantity'], 0)}</td>"
                f"<td class='r'>{de_num(li['unit_price'])}</td><td class='r'>{de_num(li['line_total'])}</td></tr>"
            )
        pt = m["msa_terms"]["payment_terms"]
        html = f"""
        {self._buyer_logo('PURCHASE ORDER', 'Bestellung')}
        <div style='height:14px'></div>
        <table style='width:100%'><tr>
          <td style='width:56%;vertical-align:top'>{self._sender_line(b)}
            <div style='font-size:10pt;line-height:1.35'>{addr_lines(s)}<br/>{s['address']['country']}</div></td>
          <td style='vertical-align:top'>{info}</td></tr></table>
        <div style='height:10px'></div>
        <p style='font-size:11pt;font-weight:bold;color:{NAVY};margin:0 0 4px 0'>Purchase Order {po['number']}</p>
        <p>Dear Mr Petersen,<br/>on the basis of the Master Supply Agreement <b>{d['msa']['number']}</b> dated
        {de_date(d['msa']['signing_date'])} we order the following goods at the agreed price-list prices. Please confirm
        this order within two business days quoting our PO number.</p>
        <table class='items'>
          <tr class='h'><th class='c'>Pos.</th><th>Item no.</th><th>Description</th><th class='c'>Unit</th>
          <th class='r'>Qty</th><th class='r'>Unit price EUR</th><th class='r'>Amount EUR</th></tr>
          {rows}
        </table>
        <table style='width:100%;margin-top:6px'><tr><td style='width:55%'></td><td>
          <table class='tot'>
            <tr><td>Net total</td><td class='r'>{self.money(t['net_total'])}</td></tr>
            <tr><td>VAT {de_num(t['vat_rate_percent'], 0)} %</td><td class='r'>{self.money(t['vat_amount'])}</td></tr>
            <tr class='g'><td>Order total (gross)</td><td class='r'>{self.money(t['gross_total'])}</td></tr>
          </table></td></tr></table>
        <table class='terms'>
          <tr><td class='k' width='26%'>Delivery address</td><td>{esc(b['name'])}, {w['name']}, {w['street']}, {w['postal_code']} {w['city']}</td></tr>
          <tr><td class='k'>Requested delivery date</td><td>{de_date(po['requested_delivery_date'])} (receiving hours Mon–Fri {w['receiving_hours'].replace(' and ', '–')})</td></tr>
          <tr><td class='k'>Delivery terms</td><td>{m['msa_terms']['incoterm']} {w['city']} (Incoterms® 2020), packaging and freight included</td></tr>
          <tr><td class='k'>Payment terms</td><td>{pt['net_days']} days net, {de_num(pt['early_payment_discount_percent'], 0)} % early-payment discount within {pt['discount_days']} days, as per MSA</td></tr>
          <tr><td class='k'>Invoices to</td><td>{b['accounts_payable']['email']} – quote PO number and delivery note number</td></tr>
        </table>
        <p style='font-size:8pt;color:{GREY}'>This order is governed exclusively by the Master Supply Agreement {d['msa']['number']}.
        Supplier terms and conditions do not apply. Surcharges of any kind are accepted only if approved in advance in writing by our Purchasing Department.</p>
        <p style='margin-top:8px'>Kind regards<br/><b>{b['contact']['name']}</b><br/>{b['contact']['role']}<br/>{esc(b['name'])}</p>
        """
        css = f"""
        body {{font-family:sans-serif;font-size:9pt;color:#222}}
        p {{margin:0 0 8px 0;line-height:1.35}}
        table.items {{width:100%;border-collapse:collapse;font-size:8pt;margin-top:4px}}
        table.items th {{background-color:{NAVY};color:white;padding:4px 4px;text-align:left;font-weight:bold}}
        table.items td {{padding:4px 4px;border-bottom:0.5px solid #c5ced8;vertical-align:top}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} .c {{text-align:center}}
        table.items th.r {{text-align:right}} table.items th.c {{text-align:center}}
        table.tot {{width:100%;border-collapse:collapse;font-size:9pt}}
        table.tot td {{padding:2px 4px}}
        table.tot tr.g td {{font-weight:bold;border-top:1px solid {NAVY};border-bottom:2px solid {NAVY};color:{NAVY}}}
        table.terms {{width:100%;border-collapse:collapse;font-size:8pt;margin:12px 0 8px 0;background-color:#f6f8fb}}
        table.terms td {{padding:3px 6px;border-bottom:0.5px solid #dde3ea;vertical-align:top}}
        td.k {{color:{NAVY};font-weight:bold}}
        """
        spec = RenderSpec([html], css, top=40, bottom=96, left=56, right=56,
                          decor=PageDecor(footer=self._buyer_footer()))
        return spec, {"title": f"Purchase Order {po['number']}", "author": b["name"], "keywords": "purchase order",
                      "creationDate": pdf_date(po["date"])}

    # ------------------------------------------------------------------ delivery note
    def delivery_note(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        dn = d["delivery_note"]
        w = b["warehouse"]
        rows = "".join(
            f"<tr><td>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td><td>{li['unit']}</td>"
            f"<td class='r'>{de_num(li['qty_ordered'], 0)}</td><td class='r'><b>{de_num(li['qty_delivered'], 0)}</b></td>"
            f"<td class='c'>{de_num(li['qty_ordered'] - li['qty_delivered'], 0)}</td></tr>"
            for li in doc_view(m)["delivery_note"]
        )
        dn_status = ("Complete delivery – no backorders" if doc_view(m)["dn_complete"]
                     else "Partial delivery – open quantities will be delivered separately")
        info = self._info_table([
            ("Delivery note no.", dn["number"]), ("Date of dispatch", de_date(dn["date"])),
            ("Your order no.", d["purchase_order"]["number"]), ("Your order date", de_date(d["purchase_order"]["date"])),
            ("Customer no.", s["customer_number_for_buyer"]), ("Contact", s["contact"]["name"]),
        ], GREEN)
        html = f"""
        {self._supplier_logo()}
        <div style='height:14px'></div>
        <table style='width:100%'><tr>
          <td style='width:56%;vertical-align:top'>{self._sender_line(s)}
            <div style='font-size:7pt;color:{GREY};margin-bottom:2px'>Delivery address:</div>
            <div style='font-size:10pt;line-height:1.35'>{esc(b['name'])}<br/>{w['name']}<br/>{w['street']}<br/>{w['postal_code']} {w['city']}</div></td>
          <td style='vertical-align:top'>{info}</td></tr></table>
        <div style='height:20px'></div>
        <p style='font-size:16pt;color:{GREEN};margin:0 0 6px 0'>Delivery Note <span style='color:#222'>{dn['number']}</span></p>
        <p>We deliver the following goods in accordance with your order {d['purchase_order']['number']}. Please check the
        goods immediately upon receipt for transport damage and completeness.</p>
        <table class='items'>
          <tr><th>Pos.</th><th>Item no.</th><th>Description</th><th>Unit</th><th class='r'>Qty ordered</th><th class='r'>Qty delivered</th><th class='c'>Backorder</th></tr>
          {rows}
        </table>
        <table class='ship'>
          <tr><td class='k' width='17%'>Packages</td><td width='38%'>{dn['packages']} (shrink-wrapped, one pallet label per pallet)</td>
              <td class='k' width='15%'>Gross weight</td><td>{dn['gross_weight_kg']} kg</td></tr>
          <tr><td class='k'>Shipping terms</td><td>{m['msa_terms']['incoterm']} {w['city']} (Incoterms® 2020)</td>
              <td class='k'>Carrier</td><td>Own truck, HH-PV 418</td></tr>
          <tr><td class='k'>Delivery status</td><td colspan='3'>{dn_status}</td></tr>
        </table>
        <table style='width:100%;margin-top:26px;font-size:8pt'><tr>
          <td style='width:46%;border-top:0.8px solid #444;padding-top:3px'>Dispatched by: {s['dispatch_contact']}, Pakvero shipping department</td>
          <td style='width:8%'></td>
          <td style='width:46%;border-top:0.8px solid #444;padding-top:3px'>Goods received (date, name, signature)</td>
        </tr></table>
        """
        css = f"""
        body {{font-family:sans-serif;font-size:9pt;color:#222}}
        p {{margin:0 0 8px 0;line-height:1.35}}
        table.items {{width:100%;border-collapse:collapse;font-size:8.3pt}}
        table.items th {{text-align:left;border-bottom:1.5px solid {GREEN};padding:4px 3px;color:{GREEN};white-space:nowrap}}
        table.items td {{padding:5px 3px;border-bottom:0.5px solid #cfd5cf;vertical-align:top}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} .c {{text-align:center}} table.items th.r {{text-align:right}} table.items th.c {{text-align:center}}
        table.ship {{width:100%;margin-top:14px;font-size:8pt;border-collapse:collapse;background-color:{GREEN_LIGHT}}}
        table.ship td {{padding:4px 6px}}
        td.k {{color:{GREEN};font-weight:bold}}
        """
        spec = RenderSpec([html], css, top=34, bottom=100, left=56, right=48,
                          decor=PageDecor(header=self._supplier_header, footer=self._supplier_footer()))
        return spec, {"title": f"Delivery Note {dn['number']}", "author": s["name"], "keywords": "delivery note",
                      "creationDate": pdf_date(dn["date"])}

    # ------------------------------------------------------------------ goods receipt (internal)
    def goods_receipt(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        gr = d["goods_receipt"]
        rows = "".join(
            f"<tr><td class='c'>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td><td class='c'>{li['unit']}</td>"
            f"<td class='r'>{de_num(li['qty_ordered'], 0)}</td><td class='r'>{de_num(li['qty_delivered'], 0)}</td>"
            f"<td class='r'><b>{de_num(li['qty_received'], 0)}</b></td>"
            f"<td class='c'>{'±0' if li['qty_received'] == li['qty_delivered'] else de_num(li['qty_received'] - li['qty_delivered'], 0)}</td>"
            f"<td class='c'>{gr['storage_location']}-{i + 1:02d}</td><td class='c'>{'OK' if li['qty_received'] == li['qty_delivered'] else 'SHORT'}</td></tr>"
            for i, li in enumerate(doc_view(m)["goods_receipt"])
        )
        view = doc_view(m)
        if view["gr_clean"]:
            gr_remark = "Delivery complete and in good condition. No deviations from purchase order or delivery note."
        elif view["gr_short_items"]:
            gr_remark = (f"Shortfall against delivery note for item(s) {', '.join(view['gr_short_items'])}; "
                         "only the quantities recorded as received were posted. Damage report sent to supplier.")
        else:
            gr_remark = "Partial delivery according to delivery note; quantities received as shown. Open PO quantities remain."
        field = lambda k, v: f"<td class='fk' width='17%'>{k}</td><td class='fv' width='33%'>{v}</td>"  # noqa: E731
        html = f"""
        {self._buyer_logo('GOODS RECEIPT', 'Wareneingangsbeleg · internal')}
        <div style='height:16px'></div>
        <table class='form'>
          <tr>{field('GR document no.', gr['number'])}{field('Posting date', de_date(gr['date']))}</tr>
          <tr>{field('Purchase order no.', d['purchase_order']['number'])}{field('PO date', de_date(d['purchase_order']['date']))}</tr>
          <tr>{field('Supplier', esc(s['name']))}{field('Supplier delivery note', d['delivery_note']['number'])}</tr>
          <tr>{field('Supplier no.', b['supplier_number_for_supplier'])}{field('Delivery note date', de_date(d['delivery_note']['date']))}</tr>
          <tr>{field('Receiving point', b['warehouse']['name'])}{field('Packages received', d['delivery_note']['packages'])}</tr>
          <tr>{field('Receiving clerk', gr['receiving_clerk'])}{field('Movement type', '101 – GR for purchase order')}</tr>
        </table>
        <div style='height:12px'></div>
        <table class='items'>
          <tr><th class='c'>Pos.</th><th>Item no.</th><th>Description</th><th class='c'>Unit</th><th class='r'>Qty PO</th>
          <th class='r'>Qty per DN</th><th class='r'>Qty received</th><th class='c'>Dev.</th><th class='c'>Bin</th><th class='c'>Cond.</th></tr>
          {rows}
        </table>
        <table class='chk'>
          <tr><td>[x] Packaging undamaged</td><td>[x] Quantities checked against delivery note</td><td>[x] Labels / batch numbers legible</td></tr>
          <tr><td>[ ] Damage report attached</td><td>[ ] Partial delivery</td><td>[ ] Quality inspection required</td></tr>
        </table>
        <p style='font-size:8pt'><b>Remarks:</b> {gr_remark}</p>
        <table style='width:100%;margin-top:22px;font-size:8pt'><tr>
          <td style='width:46%;border-top:0.8px solid #444;padding-top:3px'>Received and checked: {gr['receiving_clerk']}, Central Warehouse, {de_date(gr['date'])}</td>
          <td style='width:8%'></td>
          <td style='width:46%;border-top:0.8px solid #444;padding-top:3px'>Posted in ERP: {de_date(gr['date'])}, user JBRUEGGE</td>
        </tr></table>
        """
        css = f"""
        body {{font-family:sans-serif;font-size:8.6pt;color:#222}}
        p {{margin:6px 0}}
        table.form {{width:100%;border-collapse:collapse;font-size:8.2pt}}
        table.form td {{border:0.6px solid #9fb0c3;padding:4px 5px}}
        td.fk {{background-color:{NAVY_LIGHT};color:{NAVY};font-weight:bold}}
        table.items {{width:100%;border-collapse:collapse;font-size:7.6pt}}
        table.items th {{border:0.6px solid #9fb0c3;background-color:{NAVY_LIGHT};color:{NAVY};padding:3px 3px;text-align:left}}
        table.items td {{border:0.6px solid #9fb0c3;padding:3px 3px;vertical-align:top}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} .c {{text-align:center}} table.items th.r {{text-align:right}} table.items th.c {{text-align:center}}
        table.chk {{width:100%;font-size:7.8pt;margin-top:10px}} table.chk td {{padding:2px 0}}
        """
        spec = RenderSpec([html], css, top=40, bottom=96, left=56, right=56,
                          decor=PageDecor(footer=self._buyer_footer(internal="Form LF-LOG-07 rev. 3 · internal use only")))
        return spec, {"title": f"Goods Receipt {gr['number']}", "author": b["name"], "keywords": "goods receipt",
                      "creationDate": pdf_date(gr["date"])}

    # ------------------------------------------------------------------ invoice
    def invoice(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        view = doc_view(m)
        t = view["invoice_totals"]
        inv = d["invoice"]
        pt = m["msa_terms"]["payment_terms"]
        rows = "".join(
            f"<tr><td>{li['position']}</td><td class='ino'>{li['item_no']}</td><td>{esc(li['description'])}</td>"
            f"<td class='r'>{de_num(li['quantity'], 0)}</td><td>{li['unit']}</td>"
            f"<td class='r'>{de_num(li['unit_price'])}</td><td class='r'>{de_num(li['line_total'])}</td></tr>"
            for li in view["invoice"]
        )
        rows += "".join(
            f"<tr><td>{len(view['invoice']) + k + 1}</td><td></td><td>{esc(sc['label'])}</td><td class='r'>1</td><td>flat</td>"
            f"<td class='r'>{de_num(sc['amount'])}</td><td class='r'>{de_num(sc['amount'])}</td></tr>"
            for k, sc in enumerate(view["invoice_surcharges"])
        )
        info = self._info_table([
            ("Invoice no.", inv["number"]), ("Invoice date", de_date(inv["date"])),
            ("Delivery date", de_date(d["delivery_note"]["date"])), ("Delivery note no.", d["delivery_note"]["number"]),
            ("Your order no.", d["purchase_order"]["number"]), ("Framework agreement", d["msa"]["number"]),
            ("Customer no.", s["customer_number_for_buyer"]), ("Your VAT ID", b["vat_id"]),
        ], GREEN)
        html = f"""
        {self._supplier_logo()}
        <div style='height:14px'></div>
        <table style='width:100%'><tr>
          <td style='width:56%;vertical-align:top'>{self._sender_line(s)}
            <div style='font-size:10pt;line-height:1.35'>{esc(b['name'])}<br/>Accounts Payable<br/>{b['address']['street']}<br/>{b['address']['postal_code']} {b['address']['city']}</div></td>
          <td style='vertical-align:top'>{info}</td></tr></table>
        <div style='height:16px'></div>
        <p style='font-size:16pt;color:{GREEN};margin:0 0 6px 0'>Invoice <span style='color:#222'>{inv['number']}</span></p>
        <p>For the goods delivered with delivery note {d['delivery_note']['number']} on the basis of your purchase order
        {d['purchase_order']['number']} and our Master Supply Agreement {d['msa']['number']}, we invoice as follows:</p>
        <table class='items'>
          <tr><th>Pos.</th><th>Item no.</th><th>Description</th><th class='r'>Qty</th><th>Unit</th><th class='r'>Unit price €</th><th class='r'>Total €</th></tr>
          {rows}
        </table>
        <table style='width:100%;margin-top:4px'><tr><td style='width:52%'></td><td>
          <table class='tot'>
            <tr><td>Total net</td><td class='r'>{self.money(t['net_total'])}</td></tr>
            <tr><td>plus VAT {de_num(t['vat_rate_percent'], 0)} % on {self.money(t['net_total'])}</td><td class='r'>{self.money(t['vat_amount'])}</td></tr>
            <tr class='g'><td>Invoice total</td><td class='r'>{self.money(t['gross_total'])}</td></tr>
          </table></td></tr></table>
        <div class='pay'>
          <b>Payment terms:</b> {pt['net_days']} days net, payable by <b>{de_date(inv['due_date'])}</b> without deduction.<br/>
          For payment by {de_date(inv['discount_deadline'])} (within {pt['discount_days']} days) you may deduct
          {de_num(pt['early_payment_discount_percent'], 0)} % early-payment discount = {self.money(t['early_payment_discount_amount'])};
          amount payable: <b>{self.money(t['amount_payable_within_discount_period'])}</b>.<br/>
          Please transfer to {s['bank']['bank_name']}, IBAN {iban_grouped(s['bank']['iban'])}, BIC {s['bank']['bic']}, quoting invoice no. {inv['number']}.
        </div>
        <p style='font-size:7.5pt;color:{GREY}'>Date of supply corresponds to the delivery date. Tax number {s['tax_number']}.
        Prices according to Annex 1 of the Master Supply Agreement.</p>
        <p style='margin-top:10px'>Thank you for your order.<br/>{s['contact']['name']} · {s['contact']['role']} · {s['contact']['phone']}</p>
        """
        css = f"""
        body {{font-family:sans-serif;font-size:9pt;color:#222}}
        p {{margin:0 0 8px 0;line-height:1.35}}
        table.items {{width:100%;border-collapse:collapse;font-size:8.3pt}}
        table.items th {{text-align:left;border-bottom:1.5px solid {GREEN};padding:4px 3px;color:{GREEN};white-space:nowrap}}
        table.items td {{padding:5px 3px;border-bottom:0.5px solid #cfd5cf;vertical-align:top}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} table.items th.r {{text-align:right}}
        table.tot {{width:100%;border-collapse:collapse;font-size:9pt}}
        table.tot td {{padding:3px 3px}}
        table.tot tr.g td {{font-weight:bold;font-size:10pt;background-color:{GREEN};color:white;padding:4px 3px}}
        div.pay {{margin-top:12px;padding:6px 8px;background-color:{GREEN_LIGHT};font-size:8.3pt;line-height:1.45;border-left:3px solid {GREEN}}}
        """
        spec = RenderSpec([html], css, top=34, bottom=100, left=56, right=48,
                          decor=PageDecor(header=self._supplier_header, footer=self._supplier_footer()))
        return spec, {"title": f"Invoice {inv['number']}", "author": s["name"], "keywords": "invoice",
                      "creationDate": pdf_date(inv["date"])}

    # ------------------------------------------------------------------ MSA
    def msa(self):
        m, b, s, d = self.m, self.b, self.s, self.d
        mt = m["msa_terms"]
        pt = mt["payment_terms"]
        clauses = build_clauses("packaging")
        num = lambda prefix: clause_index(clauses, prefix)  # noqa: E731
        ctx = {
            "goods": "packaging materials (in particular corrugated cartons, films, tapes, labels and edge protectors) and fasteners (screws, nuts and washers)",
            "approval_dept": "Purchasing Department (Central Procurement)",
            "c_ordering": f"Clause {num('Ordering Process')}",
            "c_delivery_dates": f"Clause {num('Delivery Dates')}",
            "c_prices": f"Clause {num('Prices and Price List')}",
            "forecast_months": "six", "confirm_days": "two", "cancel_days": "five",
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
            "safety_weeks": "four", "insurance": "EUR 5,000,000", "liability_cap": "EUR 1,000,000",
            "conf_years": "five", "effective_date": de_date(d["msa"]["effective_date"]),
            "term_years": mt["initial_term"], "notice": mt["termination_notice"], "court": "Munich",
        }
        key_clauses = {}
        blocks = []
        for ci, c in enumerate(clauses, start=1):
            head = f"<h2>{ci}.&nbsp;&nbsp;{esc(c['title']).upper()}</h2>"
            parts = []
            for pi, para in enumerate(c["paras"], start=1):
                if isinstance(para, str):
                    para = {"text": para}
                text = para["text"].format(**ctx)
                label = f"{ci}.{pi}"
                inner = f"<p class='sc'><b class='n'>{label}</b>&nbsp;&nbsp;&nbsp;{text}</p>"
                if "items" in para:
                    inner += "".join(
                        f"<p class='li'>({chr(97 + k)})&nbsp;&nbsp;{it.format(**ctx)}</p>"
                        for k, it in enumerate(para["items"])
                    )
                parts.append(inner)
                if para.get("key"):
                    key_clauses[para["key"]] = {
                        "clause": label, "clause_title": f"{ci}. {c['title']}", "search_label": label,
                        "opening": " ".join(text.split()[:9]),
                        "summary": {"price_lock": f"Prices fixed for {mt['price_lock']['months']} months until {mt['price_lock']['end_date']}",
                                    "surcharge": "No surcharges of any kind (incl. fuel/energy) unless pre-approved in writing by Buyer's Purchasing Department",
                                    "payment_terms": f"{pt['net_days']} days net; {pt['early_payment_discount_percent']} % discount within {pt['discount_days']} days",
                                    "penalty": f"{mt['late_delivery_penalty']['rate_text']} per commenced calendar day, max {mt['late_delivery_penalty']['cap_text']} of delayed net order value"}[para["key"]],
                    }
            blocks.append((head + "".join(parts), head + parts[0][: parts[0].find("</p>") + 4]))

        cover = f"""
        <p class='kicker'>{d['msa']['number']}</p>
        <h1>MASTER SUPPLY AGREEMENT</h1>
        <p class='sub'>for packaging materials and fasteners</p>
        <p>between</p>
        <p class='party'><b>{esc(b['name'])}</b><br/>{b['address']['street']}, {b['address']['postal_code']} {b['address']['city']}, Germany<br/>
        registered with the {b['registration']['court']} under {b['registration']['number']}, represented by its managing directors
        {b['managing_directors'][0]} and {b['managing_directors'][1]}<br/>– hereinafter the <b>“Buyer”</b> –</p>
        <p>and</p>
        <p class='party'><b>{esc(s['name'])}</b><br/>{s['address']['street']}, {s['address']['postal_code']} {s['address']['city']}, Germany<br/>
        registered with the {s['registration']['court']} under {s['registration']['number']}, represented by its managing directors
        {s['managing_directors'][0]} and {s['managing_directors'][1]}<br/>– hereinafter the <b>“Supplier”</b> –</p>
        <p>– the Buyer and the Supplier each a <b>“Party”</b> and together the <b>“Parties”</b> –</p>
        <h2>PREAMBLE</h2>
        <p class='pre'>(A) The Buyer designs and manufactures conveyor systems and intralogistics equipment at its plant in
        {b['address']['city']} and ships finished assemblies and spare parts to customers throughout Europe. For this purpose it
        requires a reliable supply of standard packaging materials and standard fasteners.</p>
        <p class='pre'>(B) The Supplier is a wholesaler of industrial packaging and fastening technology with its own warehouse in
        {s['address']['city']} and supplies customers in the mechanical engineering sector from stock.</p>
        <p class='pre'>(C) Following a tender conducted by the Buyer in the fourth quarter of 2025, the Parties wish to lay down
        the terms on which the Supplier will supply such goods to the Buyer in the coming years. They therefore agree as follows:</p>
        """
        sig = f"""
        <h2>SIGNATURES</h2>
        <p>Signed in two counterparts on {de_date(d['msa']['signing_date'])}.</p>
        <table class='sig'><tr>
          <td width='46%'><b>For the Buyer</b><br/>{esc(b['name'])}<br/><br/>München, {de_date(d['msa']['signing_date'])}<br/><br/><br/>
          <div class='line'>{b['managing_directors'][0]}, Managing Director</div><br/><br/>
          <div class='line'>{b['contact']['name']}, Senior Buyer (p.p.)</div></td>
          <td width='8%'></td>
          <td width='46%'><b>For the Supplier</b><br/>{esc(s['name'])}<br/><br/>Hamburg, {de_date(d['msa']['signing_date'])}<br/><br/><br/>
          <div class='line'>{s['managing_directors'][0]}, Managing Director</div><br/><br/>
          <div class='line'>{s['managing_directors'][1]}, Managing Director</div></td>
        </tr></table>
        """
        pl_rows = "".join(
            f"<tr><td>{i}</td><td class='ino'>{p['item_no']}</td><td>{esc(p['description'])}</td><td class='c'>{p['unit']}</td><td class='r'>{de_num(p['unit_price'])}</td></tr>"
            for i, p in enumerate(m["price_list"], start=1)
        )
        annex1 = f"""
        <h2>ANNEX 1 – PRICE LIST</h2>
        <p>to Master Supply Agreement {d['msa']['number']} dated {de_date(d['msa']['signing_date'])}. Prices in EUR, net,
        exclusive of VAT, {mt['incoterm']} Delivery Address (Incoterms® 2020), including packaging and freight.
        Price Lock Period: {de_date(mt['price_lock']['start_date'])} to {de_date(mt['price_lock']['end_date'])} ({mt['price_lock']['months']} months).</p>
        <table class='pl'><tr><th>No.</th><th>Item no.</th><th>Description</th><th class='c'>Price unit</th><th class='r'>Unit price EUR</th></tr>{pl_rows}</table>
        <p style='font-size:8pt'>Minimum order value per Order: none. Quantities per Order are not restricted to full packaging units
        except where a box quantity is stated in the description.</p>
        """
        kpi_rows = "".join(f"<tr><td><b>{k}</b></td><td>{dfn}</td><td class='c'>{tgt}</td><td>{mm}</td></tr>" for k, dfn, tgt, mm in annex_kpis())
        esc_rows = "".join(f"<tr><td><b>{lv}</b></td><td>{bb}</td><td>{ss}</td><td class='c'>{rt}</td></tr>" for lv, bb, ss, rt in escalation(b, s))
        annex2 = f"""
        <h2>ANNEX 2 – DELIVERY ADDRESS, CONTACT PERSONS AND BANK DETAILS</h2>
        <table class='pl'>
          <tr><th width='22%'></th><th width='39%'>Buyer</th><th width='39%'>Supplier</th></tr>
          <tr><td>Delivery Address / Shipping point</td><td>{b['warehouse']['name']}, {b['warehouse']['street']}, {b['warehouse']['postal_code']} {b['warehouse']['city']}</td><td>{s['address']['street']}, {s['address']['postal_code']} {s['address']['city']}</td></tr>
          <tr><td>Commercial contact</td><td>{b['contact']['name']}, {b['contact']['phone']}, {b['contact']['email']}</td><td>{s['contact']['name']}, {s['contact']['phone']}, {s['contact']['email']}</td></tr>
          <tr><td>Invoices / accounts</td><td>{b['accounts_payable']['name']}, {b['accounts_payable']['email']}</td><td>{s['email']}</td></tr>
          <tr><td>VAT ID</td><td>{b['vat_id']}</td><td>{s['vat_id']}</td></tr>
          <tr><td>Bank account</td><td>{b['bank']['bank_name']}<br/>IBAN {iban_grouped(b['bank']['iban'])}</td><td>{s['bank']['bank_name']}<br/>IBAN {iban_grouped(s['bank']['iban'])}<br/>BIC {s['bank']['bic']}</td></tr>
        </table>
        <p>Changes to the contact persons may be notified in writing without amending this Agreement. Changes to the bank
        details are subject to the procedure in the clause on payment terms.</p>
        """
        annex3 = f"""
        <h2>ANNEX 3 – SUPPLIER EVALUATION AND ESCALATION</h2>
        <p>The following key figures are used for the annual supplier evaluation under the clause on supplier evaluation and continuous improvement.</p>
        <table class='pl'><tr><th width='18%'>Key figure</th><th width='40%'>Definition</th><th width='14%' class='c'>Target</th><th width='28%'>Measurement</th></tr>{kpi_rows}</table>
        <p>Disputes and operational problems are escalated as follows if they cannot be resolved at the preceding level within the stated response time:</p>
        <table class='pl'><tr><th width='22%'>Level</th><th width='31%'>Buyer</th><th width='31%'>Supplier</th><th width='16%' class='c'>Response time</th></tr>{esc_rows}</table>
        """
        css = f"""
        body {{font-family:sans-serif;font-size:9.8pt;color:#1d1d1d;line-height:1.45}}
        h1 {{font-size:20pt;color:{NAVY};margin:4px 0 2px 0;text-align:center}}
        h2 {{font-size:9.8pt;color:{NAVY};margin:13px 0 5px 0;border-bottom:0.6px solid #b8c4d3;padding-bottom:2px}}
        p {{margin:0 0 7px 0;text-align:justify}}
        p.kicker {{text-align:center;color:{GREY};font-size:9pt;margin-top:30px}}
        p.sub {{text-align:center;font-size:11pt;color:{GREY};margin-bottom:26px}}
        p.party {{margin-left:24px;text-align:left}}
        p.pre {{margin-left:0}}
        p.sc {{margin:0 0 6px 0}}
        b.n {{color:{NAVY}}}
        p.li {{margin:0 0 3px 30px;text-align:left}}
        table.sig {{width:100%;margin-top:14px}} table.sig td {{vertical-align:top}}
        div.line {{border-top:0.7px solid #333;padding-top:2px;font-size:8.5pt}}
        table.pl {{width:100%;border-collapse:collapse;font-size:8.4pt;margin:6px 0 10px 0}}
        table.pl th {{background-color:{NAVY_LIGHT};color:{NAVY};text-align:left;padding:4px;border:0.5px solid #b8c4d3}}
        table.pl td {{padding:4px;border:0.5px solid #b8c4d3;vertical-align:top}}
        td.ino {{white-space:nowrap}}
        .r {{text-align:right}} .c {{text-align:center}} table.pl th.r {{text-align:right}} table.pl th.c {{text-align:center}}
        """

        def header(page, n, total):
            if n == 1:
                return
            htmlbox(page, (64, 26, page.rect.width - 64, 44),
                    f"<div style='font-family:sans-serif;font-size:7pt;color:{GREY};border-bottom:0.5px solid #b8c4d3'>"
                    f"Master Supply Agreement {d['msa']['number']} · {esc(b['short_name'])} / {esc(s['short_name'])}</div>")

        def footer(page, n, total):
            htmlbox(page, (64, page.rect.height - 44, page.rect.width - 64, page.rect.height - 26),
                    "<table style='width:100%;font-family:sans-serif;font-size:7pt;color:#5b6470'><tr>"
                    "<td>Confidential</td>"
                    f"<td style='text-align:right'>Page {n} of {total}</td></tr></table>")

        spec = RenderSpec([[cover] + blocks + [(sig, sig)], annex1, annex2, annex3], css, top=60, bottom=62, left=70, right=70, first_top=50,
                          decor=PageDecor(header=header, footer=footer))
        meta = {"title": f"Master Supply Agreement {d['msa']['number']}", "author": f"{b['name']} / {s['name']}",
                "keywords": "master supply agreement, MSA", "creationDate": pdf_date(d["msa"]["signing_date"])}
        return spec, meta, key_clauses

    # ------------------------------------------------------------------ guideline
    def purchasing_guideline(self):
        b = self.b
        g = self.m["guideline"]
        secs = guideline_sections({**g, "buyer_name": esc(b["name"])})
        sec_blocks = [(f"<h2>{i}&nbsp;&nbsp;{t}</h2>{h}",) * 2 for i, (t, h) in enumerate(secs, start=1)]
        html = f"""
        {self._buyer_logo('PURCHASING GUIDELINE', 'Internal policy · ' + g['number'])}
        <div style='height:14px'></div>
        <h1>Procurement and Invoice Verification Guideline</h1>
        <table class='dc'>
          <tr><td class='k' width='16%'>Document no.</td><td width='34%'>{g['number']}</td><td class='k' width='16%'>Version</td><td>{g['version']}</td></tr>
          <tr><td class='k'>Valid from</td><td>{de_date(g['valid_from'])}</td><td class='k'>Owner</td><td>{g['owner']}</td></tr>
          <tr><td class='k'>Approved by</td><td colspan='3'>{g['approved_by']}</td></tr>
          <tr><td class='k'>Distribution</td><td colspan='3'>Purchasing, Central Warehouse, Accounts Payable, all budget owners</td></tr>
        </table>
        """
        closing = f"""<p style='margin-top:14px;font-size:8pt;color:{GREY}'>Questions regarding this guideline: Purchasing Department, {b['contact']['email']}.
        This document is for internal use only and must not be passed on to suppliers.</p>"""
        css = f"""
        body {{font-family:sans-serif;font-size:9.2pt;color:#222;line-height:1.4}}
        h1 {{font-size:14pt;color:{NAVY};margin:0 0 8px 0}}
        h2 {{font-size:10.5pt;color:{NAVY};margin:12px 0 4px 0}}
        p {{margin:0 0 6px 0}}
        ol {{margin:2px 0 6px 0}} li {{margin-bottom:2px}}
        table.dc {{width:100%;border-collapse:collapse;font-size:8pt;margin-bottom:6px}}
        table.dc td {{border:0.5px solid #b8c4d3;padding:3px 5px}} td.k {{background-color:{NAVY_LIGHT};color:{NAVY};font-weight:bold}}
        table.tbl {{width:100%;border-collapse:collapse;font-size:8.3pt;margin:4px 0 8px 0}}
        table.tbl th {{background-color:{NAVY};color:white;text-align:left;padding:4px}}
        table.tbl td {{border-bottom:0.5px solid #b8c4d3;padding:4px;vertical-align:top}}
        div.note {{background-color:#fff4e5;border-left:3px solid #c77700;padding:6px 8px;font-size:8.5pt;margin:4px 0 8px 0}}
        """
        spec = RenderSpec([[html] + sec_blocks + [closing]], css, top=40, bottom=96, left=56, right=56,
                          decor=PageDecor(footer=self._buyer_footer(internal=f"{g['number']} v{g['version']} · internal")))
        return spec, {"title": f"Purchasing Guideline {g['number']}", "author": b["name"], "keywords": "purchasing guideline",
                      "creationDate": pdf_date(g["valid_from"])}
