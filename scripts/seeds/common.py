"""Shared helpers for the synthetic seed procurement packages.

Everything here is deterministic: money arithmetic with Decimal (ROUND_HALF_UP),
German number/date formatting, HTML->PDF rendering via ``pymupdf.Story``,
post-hoc header/footer stamping, PDF text verification and clause page lookup.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Callable

import pymupdf

REPO = Path(__file__).resolve().parents[2]
SEEDS_OUT = REPO / "data" / "seeds"
PREVIEW_DIR = REPO / "data" / "seed_previews"  # PNG previews of every page (git-ignored)

CENT = Decimal("0.01")
SYNTHETIC_SUBJECT = "synthetic test data"


# --------------------------------------------------------------------------- money / numbers
def D(value) -> Decimal:
    return Decimal(str(value))


def q2(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


def s2(value: Decimal) -> str:
    """Canonical JSON money string, e.g. '1234.56'."""
    return str(q2(value))


def de_num(value, decimals: int = 2) -> str:
    """German number format: 1.234,56 (decimals=0 -> 1.234)."""
    v = Decimal(value)
    if decimals:
        v = v.quantize(Decimal(1).scaleb(-decimals), rounding=ROUND_HALF_UP)
        s = f"{v:,.{decimals}f}"
    else:
        s = f"{int(v):,}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def parse_de(text: str) -> Decimal:
    """Parse a German formatted number ('1.234,56' / '1.200' / '19,00')."""
    t = text.strip().replace("€", "").replace("EUR", "").replace("%", "").strip()
    t = t.replace(".", "").replace(",", ".")
    return Decimal(t)


def de_date(iso: str) -> str:
    d = date.fromisoformat(iso)
    return d.strftime("%d.%m.%Y")


def iban_checksum(country: str, bban: str) -> str:
    """Build an IBAN with a valid mod-97 checksum from a (fictional) BBAN."""
    rearranged = bban + country + "00"
    digits = "".join(str(int(c, 36)) for c in rearranged)
    check = 98 - int(digits) % 97
    return f"{country}{check:02d}{bban}"


def iban_grouped(iban: str) -> str:
    return " ".join(iban[i : i + 4] for i in range(0, len(iban), 4))


# --------------------------------------------------------------------------- master data
def compute_master(cfg: dict) -> dict:
    """Return master data with all computed amounts (as canonical strings) and assert them."""
    vat_rate = D(cfg["vat_rate"])
    price_map = {p["item_no"]: D(p["unit_price"]) for p in cfg["price_list"]}
    lines = []
    net = Decimal("0")
    for pos, li in enumerate(cfg["order_items"], start=1):
        qty = D(li["quantity"])
        price = D(li["unit_price"])
        assert price == price_map[li["item_no"]], f"PO price deviates from MSA price list: {li['item_no']}"
        total = q2(qty * price)
        net += total
        lines.append(
            {
                "position": pos * cfg.get("position_step", 1),
                "item_no": li["item_no"],
                "description": li["description"],
                "unit": li["unit"],
                "quantity": int(qty),
                "unit_price": s2(price),
                "line_total": s2(total),
            }
        )
    assert 6 <= len(lines) <= 8
    net = q2(net)
    vat = q2(net * vat_rate / 100)
    gross = q2(net + vat)
    terms = cfg["msa_terms"]["payment_terms"]
    disc_pct = D(terms["early_payment_discount_percent"])
    discount = q2(gross * disc_pct / 100)
    payable_disc = q2(gross - discount)

    # independent re-check
    assert sum(D(li["line_total"]) for li in lines) == net
    assert q2(net * Decimal("0.19")) == vat and vat_rate == Decimal("19")
    assert net + vat == gross
    assert gross - discount == payable_disc

    master = {k: v for k, v in cfg.items() if k not in ("order_items", "position_step")}
    master["line_items"] = lines
    master["totals"] = {
        "net_total": s2(net),
        "vat_rate_percent": s2(vat_rate),
        "vat_amount": s2(vat),
        "gross_total": s2(gross),
        "early_payment_discount_percent": s2(disc_pct),
        "early_payment_discount_amount": s2(discount),
        "amount_payable_within_discount_period": s2(payable_disc),
    }
    return master


# --------------------------------------------------------------------------- rendering
@dataclass
class PageDecor:
    """Callable stamping applied to every page after the story is laid out."""

    header: Callable[[pymupdf.Page, int, int], None] | None = None
    footer: Callable[[pymupdf.Page, int, int], None] | None = None


@dataclass
class RenderSpec:
    sections: list  # each section starts on a new page; str or list of blocks
    css: str
    top: float = 60
    bottom: float = 70
    left: float = 56
    right: float = 56
    first_top: float | None = None  # different top margin on page 1
    decor: PageDecor = field(default_factory=PageDecor)


def _measure(html: str, css: str, width: float) -> float:
    story = pymupdf.Story(html, user_css=css)
    _, filled = story.place(pymupdf.Rect(0, 0, width, 10_000))
    return pymupdf.Rect(filled).height


def render_pdf(path: Path, spec: RenderSpec, metadata: dict) -> int:
    """Lay out ``spec.sections``; each section starts on a new page.

    A section is either one HTML string or a list of blocks. A block is an HTML string or a
    ``(html, keep_html)`` tuple: if the height of ``keep_html`` (e.g. heading + first sub-clause)
    does not fit on the current page, the block starts on a new page (keep-with-next).
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    mediabox = pymupdf.paper_rect("a4")
    width = mediabox.width - spec.left - spec.right
    bottom = mediabox.height - spec.bottom
    tmp = path.with_suffix(".tmp.pdf")
    writer = pymupdf.DocumentWriter(str(tmp))
    page_no = 0
    dev = None

    def new_page():
        nonlocal dev, page_no
        if dev is not None:
            writer.end_page()
        dev = writer.begin_page(mediabox)
        page_no += 1
        return spec.first_top if (page_no == 1 and spec.first_top is not None) else spec.top

    for section in spec.sections:
        blocks = [section] if isinstance(section, str) else section
        y = new_page()
        top_of_page = y
        for block in blocks:
            html, keep = (block, None) if isinstance(block, str) else block
            if keep is not None and y > top_of_page and y + _measure(keep, spec.css, width) > bottom:
                y = top_of_page = new_page()
            story = pymupdf.Story(html, user_css=spec.css)
            while True:
                more, filled = story.place(pymupdf.Rect(spec.left, y, spec.left + width, bottom))
                story.draw(dev)
                if not more:
                    y = pymupdf.Rect(filled).y1
                    break
                y = top_of_page = new_page()
    writer.end_page()
    writer.close()

    doc = pymupdf.open(str(tmp))
    total = doc.page_count
    for i, page in enumerate(doc):
        if spec.decor.header:
            spec.decor.header(page, i + 1, total)
        if spec.decor.footer:
            spec.decor.footer(page, i + 1, total)
    meta = {
        "title": metadata.get("title", ""),
        "author": metadata.get("author", ""),
        "subject": SYNTHETIC_SUBJECT,
        "keywords": f"{SYNTHETIC_SUBJECT}; {metadata.get('keywords', '')}".strip("; "),
        "creator": "Agent On Duty seed generator (THWS research project)",
        "producer": "PyMuPDF",
        "creationDate": metadata.get("creationDate", ""),
        "modDate": metadata.get("creationDate", ""),
    }
    doc.set_metadata(meta)
    doc.subset_fonts()
    doc.save(str(path), garbage=3, deflate=True)
    doc.close()
    tmp.unlink()
    return total


def pdf_date(iso: str) -> str:
    return "D:" + iso.replace("-", "") + "090000+01'00'"


def htmlbox(page: pymupdf.Page, rect, html: str, css: str = "") -> None:
    rc = page.insert_htmlbox(pymupdf.Rect(rect), html, css=css)
    if rc[0] < 0:
        raise RuntimeError(f"htmlbox overflow on page {page.number + 1}: {html[:80]}")


def preview(path: Path, package: str, dpi: int = 60) -> list[Path]:
    out = []
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(path))
    for i, page in enumerate(doc):
        p = PREVIEW_DIR / f"{package}__{path.stem}__p{i + 1:02d}.png"
        page.get_pixmap(dpi=dpi).save(str(p))
        out.append(p)
    return out


def esc(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# --------------------------------------------------------------------------- verification
class VerificationError(AssertionError):
    pass


def pdf_text(path: Path) -> list[str]:
    doc = pymupdf.open(str(path))
    pages = [p.get_text() for p in doc]
    doc.close()
    return pages


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


NUM_RE = re.compile(r"^-?\d{1,3}(?:\.\d{3})*(?:,\d+)?$|^-?\d+(?:,\d+)?$")


def row_numbers(path: Path, anchor: str) -> list[Decimal]:
    """Find the table row whose words include ``anchor`` and return all German numbers on it."""
    doc = pymupdf.open(str(path))
    hits = []
    for page in doc:
        words = page.get_text("words")
        for w in words:
            if w[4] == anchor:
                y0, y1 = w[1], w[3]
                mid = (y0 + y1) / 2
                row = [x for x in words if x[1] <= mid <= x[3] and x[0] >= w[0]]
                row.sort(key=lambda x: x[0])
                nums = []
                for x in row[1:]:
                    tok = x[4].replace("€", "")
                    if NUM_RE.match(tok):
                        nums.append(parse_de(tok))
                hits.append(nums)
    doc.close()
    if len(hits) != 1:
        raise VerificationError(f"{path.name}: anchor {anchor!r} found {len(hits)}x as a row (expected 1)")
    return hits[0]


def require(text: str, needle: str, where: str, errors: list[str]) -> None:
    if norm_ws(needle) not in norm_ws(text):
        errors.append(f"{where}: missing {needle!r}")


def label_value(text: str, label: str) -> str | None:
    """Return the token that follows ``label`` in whitespace-normalised text."""
    t = norm_ws(text)
    idx = t.find(label)
    if idx < 0:
        return None
    rest = t[idx + len(label) :].strip().lstrip(":").strip()
    return rest.split(" ")[0] if rest else None


def find_clause_page(path: Path, label: str, opening: str) -> dict:
    """Locate the page on which a numbered sub-clause starts, by searching extracted text."""
    pages = pdf_text(path)
    needle = norm_ws(f"{label} {opening}")
    found = [i + 1 for i, t in enumerate(pages) if needle in norm_ws(t)]
    if len(found) != 1:
        # the opening may wrap across a page break: fall back to label + first 4 words
        short = norm_ws(f"{label} " + " ".join(opening.split()[:4]))
        found = [i + 1 for i, t in enumerate(pages) if short in norm_ws(t)]
    if len(found) != 1:
        raise VerificationError(f"{path.name}: clause {label!r} located on pages {found} (expected exactly one)")
    return {"page": found[0], "page_count": len(pages)}


def dump_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
