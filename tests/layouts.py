"""Unseen invoice / PO layouts for extraction robustness tests (not used by the benchmark)."""

from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

import pymupdf

Q = Decimal("0.01")


def _render(html: str, css: str, path: Path):
    story = pymupdf.Story(html=html, user_css=css)
    writer = pymupdf.DocumentWriter(str(path))
    mediabox = pymupdf.paper_rect("a4")
    where = mediabox + (45, 50, -45, -60)
    more = True
    while more:
        dev = writer.begin_page(mediabox)
        more, _ = story.place(where)
        story.draw(dev)
        writer.end_page()
    writer.close()


def _de(v: Decimal) -> str:
    s = f"{v:,.2f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def german_invoice(path: Path) -> dict:
    """German labels, numeric article numbers, € inside the cells, a freight line, Nettobetrag/MwSt/Rechnungsbetrag."""
    lines = [("100234", "Sechskantschraube M6x20 verzinkt", 250, Decimal("0.12")),
             ("100771", "Unterlegscheibe 6,4 mm", 500, Decimal("0.03")),
             ("204410", "Kabelbinder 200 mm schwarz (100 Stk.)", 12, Decimal("4.90")),
             ("310005", "Klebeband 50 mm x 66 m", 36, Decimal("2.35"))]
    rows, net = "", Decimal(0)
    for i, (no, desc, qty, price) in enumerate(lines, 1):
        total = (qty * price).quantize(Q)
        net += total
        rows += (f"<tr><td>{i}</td><td>{no}</td><td>{desc}</td><td class='r'>{qty:,}".replace(",", ".") +
                 f"</td><td class='r'>{_de(price)} €</td><td class='r'>{_de(total)} €</td></tr>")
    freight = Decimal("45.00")
    rows += f"<tr><td>5</td><td></td><td>Frachtkostenzuschlag</td><td class='r'>1</td><td class='r'>{_de(freight)} €</td><td class='r'>{_de(freight)} €</td></tr>"
    net += freight
    vat = (net * Decimal("0.19")).quantize(Q, ROUND_HALF_UP)
    html = f"""<h1>Rechnung Nr. 2026-4711</h1>
    <p>Bestellnummer: B-55120 · Rahmenvertrag RV-2026-17</p>
    <table class='t'><tr><th>Pos.</th><th>Artikelnr.</th><th>Bezeichnung</th><th class='r'>Menge</th>
    <th class='r'>Einzelpreis</th><th class='r'>Gesamtpreis</th></tr>{rows}</table>
    <table class='s'><tr><td>Nettobetrag</td><td class='r'>{_de(net)} €</td></tr>
    <tr><td>MwSt. 19 %</td><td class='r'>{_de(vat)} €</td></tr>
    <tr><td><b>Rechnungsbetrag</b></td><td class='r'><b>{_de(net + vat)} €</b></td></tr></table>"""
    css = ("body{font-family:sans-serif;font-size:9pt} h1{font-size:16pt} table.t{width:100%;border-collapse:collapse}"
           "table.t th{text-align:left;border-bottom:1px solid #000;padding:3px} table.t td{padding:3px}"
           ".r{text-align:right} table.s{width:45%;margin-left:55%;margin-top:10px}")
    _render(html, css, path)
    return {"lines": [(no, Decimal(qty), price, (qty * price).quantize(Q)) for no, _, qty, price in lines],
            "surcharges": [("Frachtkostenzuschlag", freight)], "net": net, "vat": vat, "gross": net + vat}


def english_multipage_invoice(path: Path) -> dict:
    """English labels and number format (1,234.56), SKUs without dashes, 40 lines over two pages (header repeated)."""
    lines = [(f"X{4000 + i * 7}", f"Component type {i}, industrial grade", (i % 9 + 1) * 25, (Decimal(i * 37 % 900) + 105) / 100)
             for i in range(1, 41)]
    rows, net = "", Decimal(0)
    for no, desc, qty, price in lines:
        total = (qty * price).quantize(Q)
        net += total
        rows += f"<tr><td>{no}</td><td>{desc}</td><td class='r'>{qty:,}</td><td class='r'>{price:,.2f}</td><td class='r'>{total:,.2f}</td></tr>"
    vat = (net * Decimal("0.19")).quantize(Q, ROUND_HALF_UP)
    html = f"""<h1>INVOICE 88-20417</h1><p>Customer PO: 7700913 · Currency EUR</p>
    <table class='t'><thead><tr><th>SKU</th><th>Description</th><th class='r'>Qty</th><th class='r'>Unit Cost</th>
    <th class='r'>Amount</th></tr></thead>{rows}</table>
    <table class='s'><tr><td>Subtotal</td><td class='r'>{net:,.2f}</td></tr><tr><td>VAT 19%</td><td class='r'>{vat:,.2f}</td></tr>
    <tr><td><b>Total due</b></td><td class='r'><b>{net + vat:,.2f}</b></td></tr></table>"""
    css = ("body{font-family:sans-serif;font-size:9pt} h1{font-size:16pt} table.t{width:100%;border-collapse:collapse}"
           "table.t th{text-align:left;border-bottom:1px solid #000;padding:3px} table.t td{padding:4px 3px}"
           ".r{text-align:right} table.s{width:40%;margin-left:60%;margin-top:10px}")
    _render(html, css, path)
    return {"lines": [(no, Decimal(qty), price, (qty * price).quantize(Q)) for no, _, qty, price in lines],
            "surcharges": [], "net": net, "vat": vat, "gross": net + vat}
