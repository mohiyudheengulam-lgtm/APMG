"""Path B — OKF v0.2 concept navigation (Exposé §5.2).

Bundle per package:
    index.md                      package overview, links to every concept
    invoice.md / purchase_order.md / delivery_note.md / goods_receipt.md   one concept per document
    guideline.md                  the buyer's purchasing guideline (full text)
    msa/index.md                  list of MSA sections with their pages
    msa/<section>.md              one concept per MSA section / annex, with "[page N]" markers
Each concept has YAML frontmatter (type, source_document, page, pages[, clause_id]) and Markdown links.
The agent navigates with read(path) only — no embeddings.
"""

import json
import re
import time
from pathlib import Path

import yaml

from agent_on_duty.extraction.extract import DocType, ExtractedDocument, extract_package

NUMBERED_RE = re.compile(r"^(\d{1,2})\.\s+([A-Z][A-Z0-9 ,&/\-–’'()]{3,})$")   # "27.  SURCHARGES AND ..."
PARAGRAPH_RE = re.compile(r"^§\s*(\d{1,2})$")                                     # "§ 28" + title on next line
ANNEX_RE = re.compile(r"^(ANNEX|Annex|Schedule|SCHEDULE)\s+(\d+)(\s*[–-]\s*(.+))?$")
PREAMBLE_RE = re.compile(r"^(PREAMBLE|Preamble|RECITALS|Recitals)$")
TITLES = {DocType.INVOICE: "Invoice", DocType.PURCHASE_ORDER: "Purchase Order", DocType.GOODS_RECEIPT: "Goods Receipt",
          DocType.DELIVERY_NOTE: "Delivery Note"}


def _frontmatter(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n\n"


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _record_concept(doc: ExtractedDocument, links: list[tuple[str, str]]) -> str:
    rec = doc.record
    priced = doc.doc_type in (DocType.INVOICE, DocType.PURCHASE_ORDER)
    meta = {"type": doc.doc_type.value, "title": f"{TITLES[doc.doc_type]} {doc.filename.removesuffix('.pdf')}",
            "source_document": doc.filename, "page": 1, "pages": [1]}
    body = [f"# {meta['title']}", ""]
    header = {k: v for k, v in rec.model_dump(exclude={"lines", "surcharges", "source"}).items() if v is not None}
    body += [f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in header.items()] + [""]
    if priced:
        body += ["| Item | Description | Qty | Unit Price | Line Total |", "|---|---|---|---|---|"]
        body += [f"| {ln.item_no} | {ln.description} | {ln.quantity} | {ln.unit_price} | {ln.line_total} |" for ln in rec.lines]
    else:
        label = "Qty Received" if doc.doc_type == DocType.GOODS_RECEIPT else "Qty Delivered"
        body += [f"| Item | {label} |", "|---|---|"]
        body += [f"| {ln.item_no} | {ln.quantity} |" for ln in rec.lines]
    if getattr(rec, "surcharges", None):
        body += ["", "## Additional Charges", ""] + [f"- {s.label}: {s.amount}" for s in rec.surcharges]
    if links:
        body += ["", "## Related", ""] + [f"- [{label}]({target})" for label, target in links]
    return _frontmatter(meta) + "\n".join(body) + "\n"


def _msa_sections(doc: ExtractedDocument) -> list[dict]:
    """Split the contract at clause / annex headings; text keeps "[page N]" markers for citation."""
    sections: list[dict] = []
    cur = {"clause_id": "front", "title": "Cover and contents", "lines": [], "pages": []}

    def add_line(page: int, line: str):
        if page not in cur["pages"]:
            cur["pages"].append(page)
            cur["lines"].append(f"[page {page}]")
        cur["lines"].append(line)

    def heading_count(lines: list[str]) -> int:
        return sum(bool(NUMBERED_RE.match(ln) or PARAGRAPH_RE.match(ln)) for ln in lines)

    for p in doc.pages:
        lines = [ln.strip() for ln in p.text.splitlines()]
        toc = heading_count(lines) > 8  # a table of contents, not clause text: keep it in the front matter
        i = 0
        while i < len(lines):
            ln = lines[i]
            head = None
            if toc:
                pass
            elif m := NUMBERED_RE.match(ln):
                head = (m.group(1), m.group(2).title())
            elif (m := PARAGRAPH_RE.match(ln)) and i + 1 < len(lines) and lines[i + 1]:
                head = (f"§ {m.group(1)}", lines[i + 1])
                i += 1
            elif (m := ANNEX_RE.match(ln)) and ";" not in ln:
                title = m.group(4) or (lines[i + 1] if i + 1 < len(lines) else "")
                if m.group(4) is None:
                    i += 1
                head = (f"Annex {m.group(2)}", title)
            elif PREAMBLE_RE.match(ln):
                head = ("Preamble", "Preamble")
            if head:
                sections.append(cur)
                cur = {"clause_id": head[0], "title": head[1].strip(), "lines": [], "pages": []}
                add_line(p.page, f"{head[0]} {head[1]}".strip())
            elif ln:
                add_line(p.page, ln)
            i += 1
    sections.append(cur)
    return [s for s in sections if any(not l.startswith("[page") for l in s["lines"])]


def _msa_concepts(doc: ExtractedDocument) -> dict[str, str]:
    files, index_lines, used = {}, [], set()
    for sec in _msa_sections(doc):
        name = f"{_slug(sec['clause_id'] + ' ' + sec['title'])[:60]}.md"
        while name in used:
            name = name.replace(".md", "_2.md")
        used.add(name)
        meta = {"type": "msa_section", "title": sec["title"], "clause_id": sec["clause_id"],
                "source_document": doc.filename, "page": sec["pages"][0], "pages": sec["pages"]}
        pages = f"page {sec['pages'][0]}" if len(sec["pages"]) == 1 else f"pages {sec['pages'][0]}–{sec['pages'][-1]}"
        files[f"msa/{name}"] = _frontmatter(meta) + f"# {sec['clause_id']} {sec['title']}\n\n" + "\n".join(sec["lines"]) \
            + "\n\n[MSA index](index.md)\n"
        index_lines.append(f"- [{sec['clause_id']} {sec['title']}]({name}) — {pages}")
    files["msa/index.md"] = _frontmatter({"type": "index", "title": f"MSA {doc.filename}", "source_document": doc.filename}) \
        + f"# Master agreement ({doc.filename}) — sections\n\n" + "\n".join(index_lines) + "\n\n[Package index](../index.md)\n"
    return files


def _text_concept(doc: ExtractedDocument, title: str) -> str:
    meta = {"type": doc.doc_type.value, "title": title, "source_document": doc.filename, "page": 1,
            "pages": [p.page for p in doc.pages]}
    body = "\n".join(f"[page {p.page}]\n{p.text.strip()}" for p in doc.pages)
    return _frontmatter(meta) + f"# {title}\n\n{body}\n\n[Package index](index.md)\n"


def _msa_link(files: dict[str, str], *keywords: str) -> str | None:
    return next((p for p in files if p.startswith("msa/") and p != "msa/index.md" and any(k in p for k in keywords)), None)


def convert_contract(doc: ExtractedDocument, out_dir: Path) -> dict:
    """Concept files for one library contract (msa/...) or guideline (guideline.md); built once, mounted into packages."""
    t0 = time.perf_counter()
    files = _msa_concepts(doc) if doc.doc_type == DocType.MSA else \
        {"guideline.md": _text_concept(doc, f"Purchasing guideline ({doc.filename})")}
    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / rel).write_text(content, encoding="utf-8")
    stats = {"path": "B", "concepts": len(files), "build_seconds": round(time.perf_counter() - t0, 3),
             "storage_bytes": sum(f.stat().st_size for f in out_dir.rglob("*.md"))}
    (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
    return stats


def convert(package_dir: Path, out_dir: Path, pkg=None, t_extract: float | None = None,
            mounts: dict[str, Path] | None = None) -> dict:
    """Write the package's OKF bundle. `mounts` = library contract folders ("msa", "guideline.md") linked in.
    Returns preparation stats (criterion 4)."""
    t0 = time.perf_counter()
    if pkg is None:
        pkg = extract_package(package_dir)
        t_extract = time.perf_counter() - t0
    mounts = mounts or {}

    files: dict[str, str] = {}
    msa = pkg.get(DocType.MSA)
    if msa:
        files.update(_msa_concepts(msa))
    elif "msa" in mounts:  # contract from the library: only the file names are needed for the links
        files.update({f"msa/{f.name}": "" for f in (mounts["msa"]).glob("*.md")})
    guideline = pkg.get(DocType.GUIDELINE)
    if guideline:
        files["guideline.md"] = _text_concept(guideline, f"Purchasing guideline ({guideline.filename})")
    present = {d.doc_type: f"{d.doc_type.value}.md" for d in pkg.documents if d.doc_type in TITLES}
    pricing, surcharges = _msa_link(files, "price", "pric"), _msa_link(files, "surcharge", "charge")
    price_list = _msa_link(files, "annex_1")
    for d in pkg.documents:
        if d.doc_type not in TITLES:
            continue
        links = [(TITLES[t], f) for t, f in present.items() if t != d.doc_type]
        if d.doc_type == DocType.INVOICE:
            links += [(label, target) for label, target in
                      (("MSA pricing clause", pricing), ("MSA price list annex", price_list),
                       ("MSA surcharge clause", surcharges)) if target]
        files[present[d.doc_type]] = _record_concept(d, links)

    missing = [t.value for t in TITLES if t not in present]
    index = [f"# Procurement package {pkg.package_id}", "", "## Documents", ""]
    index += [f"- [{TITLES[t]}]({f})" for t, f in present.items()]
    if msa or "msa" in mounts:
        index += ["- [Master agreement (MSA) — sections](msa/index.md)" + ("" if msa else " · from the contract library")]
    if guideline or "guideline.md" in mounts:
        index += ["- [Purchasing guideline](guideline.md)" + ("" if guideline else " · from the contract library")]
    if missing:
        index += ["", "## Not in package", ""] + [f"- {m}" for m in missing]
    files["index.md"] = _frontmatter({"type": "index", "title": pkg.package_id}) + "\n".join(index) + "\n"

    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        if not content:  # mounted from the library
            continue
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / rel).write_text(content, encoding="utf-8")
    stats = {
        "path": "B", "package_id": pkg.package_id, "concepts": sum(1 for c in files.values() if c),
        "extract_seconds": round(t_extract or 0, 3), "build_seconds": round(time.perf_counter() - t0 + (t_extract or 0), 3),
        "storage_bytes": sum(f.stat().st_size for f in out_dir.rglob("*.md")),
        "documents": [{"file": d.filename, "type": d.doc_type.value} for d in pkg.documents],
    }
    (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
    return stats


class PathBBundle:
    def __init__(self, root: Path, mounts: dict[str, Path] | None = None):
        """`mounts`: library contract folders shown inside the bundle, e.g. {"msa": .../msa, "guideline.md": ...}."""
        self.root = root.resolve()
        self.mounts = {k: v.resolve() for k, v in (mounts or {}).items()}

    def _resolve(self, path: str) -> tuple[Path, Path]:
        rel = path.strip().lstrip("/")
        head, _, rest = rel.partition("/")
        if head in self.mounts and self.mounts[head].is_dir():
            return self.mounts[head], (self.mounts[head] / rest).resolve()
        if rel in self.mounts:
            return self.mounts[rel].parent, self.mounts[rel]
        return self.root, (self.root / rel).resolve()

    def read(self, path: str) -> str:
        """Open a concept or index file; paths are relative to the bundle root and sandboxed to it (or a mount)."""
        base, target = self._resolve(path)
        if base not in target.parents and target != base:
            raise ValueError("path outside bundle")
        if target.is_dir():
            target = target / "index.md"
        if not target.exists() or target.suffix != ".md":
            raise FileNotFoundError(path)
        return target.read_text(encoding="utf-8")

    def meta(self, path: str) -> dict:
        text = self.read(path)
        return yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}
