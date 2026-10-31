"""Path B — OKF v0.2 concept navigation (Exposé §5.2).

Bundle per package:
    index.md                      package overview, links to every concept
    invoice.md / purchase_order.md / goods_receipt.md   one concept per document
    msa/index.md                  list of MSA sections
    msa/<topic>.md                one concept per MSA section
Each concept has YAML frontmatter (type, source_document, page[, clause_id]) and Markdown links.
The agent navigates with read(path) only — no embeddings.
"""

import json
import re
import time
from pathlib import Path

import yaml

from agent_on_duty.extraction.extract import DocType, ExtractedDocument, extract_package

SECTION_RE = re.compile(r"^Section (\d+)\. (.+)$", re.M)
TITLES = {DocType.INVOICE: "Invoice", DocType.PURCHASE_ORDER: "Purchase Order", DocType.GOODS_RECEIPT: "Goods Receipt"}


def _frontmatter(meta: dict) -> str:
    return "---\n" + yaml.safe_dump(meta, sort_keys=False).strip() + "\n---\n\n"


def _slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", title.lower()).strip("_")


def _record_concept(doc: ExtractedDocument, links: list[tuple[str, str]]) -> str:
    rec = doc.record
    priced = doc.doc_type != DocType.GOODS_RECEIPT
    meta = {"type": doc.doc_type.value, "title": f"{TITLES[doc.doc_type]} {doc.filename.removesuffix('.pdf')}",
            "source_document": doc.filename, "page": 1}
    body = [f"# {meta['title']}", ""]
    header = {k: v for k, v in rec.model_dump(exclude={"lines", "surcharges", "source"}).items() if v is not None}
    body += [f"- **{k.replace('_', ' ').title()}:** {v}" for k, v in header.items()] + [""]
    if priced:
        body += ["| Item | Description | Qty | Unit Price | Line Total |", "|---|---|---|---|---|"]
        body += [f"| {ln.item_no} | {ln.description} | {ln.quantity} | {ln.unit_price} | {ln.line_total} |" for ln in rec.lines]
    else:
        body += ["| Item | Description | Qty Received |", "|---|---|---|"]
        body += [f"| {ln.item_no} | {ln.description} | {ln.quantity} |" for ln in rec.lines]
    if getattr(rec, "surcharges", None):
        body += ["", "## Additional Charges", ""] + [f"- {s.label}: {s.amount}" for s in rec.surcharges]
    if links:
        body += ["", "## Related", ""] + [f"- [{label}]({target})" for label, target in links]
    return _frontmatter(meta) + "\n".join(body) + "\n"


def _msa_concepts(doc: ExtractedDocument) -> dict[str, str]:
    """One concept per MSA section; each section starts on its own page in the benchmark corpus."""
    files, index_lines = {}, []
    for p in doc.pages:
        m = SECTION_RE.search(p.text)
        if not m:
            continue
        clause_id, title = m.group(1), m.group(2).strip()
        name = f"{_slug(title)}.md"
        text = p.text[m.start():].strip()
        text = re.sub(r"\n?Page \d+\s*$", "", text)
        meta = {"type": "msa_section", "title": title, "clause_id": clause_id,
                "source_document": doc.filename, "page": p.page}
        files[f"msa/{name}"] = _frontmatter(meta) + f"# §{clause_id} {title}\n\n{text}\n\n[MSA index](index.md)\n"
        index_lines.append(f"- [§{clause_id} {title}]({name}) — page {p.page}")
    files["msa/index.md"] = _frontmatter({"type": "index", "title": f"MSA {doc.filename}", "source_document": doc.filename}) \
        + f"# Master Service Agreement ({doc.filename})\n\n" + "\n".join(index_lines) + "\n\n[Package index](../index.md)\n"
    return files


def _msa_link(files: dict[str, str], keyword: str) -> str | None:
    return next((p for p in files if p.startswith("msa/") and keyword in p), None)


def convert(package_dir: Path, out_dir: Path) -> dict:
    """Extract raw PDFs and write the OKF bundle. Returns preparation stats (criterion 4)."""
    t0 = time.perf_counter()
    pkg = extract_package(package_dir)
    t_extract = time.perf_counter() - t0

    files: dict[str, str] = {}
    msa = pkg.get(DocType.MSA)
    if msa:
        files.update(_msa_concepts(msa))
    present = {d.doc_type: f"{d.doc_type.value}.md" for d in pkg.documents if d.doc_type != DocType.MSA}
    pricing, surcharges = _msa_link(files, "pric"), _msa_link(files, "charge")
    for d in pkg.documents:
        if d.doc_type == DocType.MSA:
            continue
        links = [(TITLES[t], f) for t, f in present.items() if t != d.doc_type]
        if d.doc_type == DocType.INVOICE:
            links += [(label, target) for label, target in
                      (("MSA pricing clause", pricing), ("MSA surcharge clause", surcharges)) if target]
        files[present[d.doc_type]] = _record_concept(d, links)

    missing = [t.value for t in TITLES if t not in present]
    index = [f"# Procurement package {pkg.package_id}", "", "## Documents", ""]
    index += [f"- [{TITLES[t]}]({f})" for t, f in present.items()]
    if msa:
        index += [f"- [Master Service Agreement](msa/index.md)"]
    if missing:
        index += ["", "## Not in package", ""] + [f"- {m}" for m in missing]
    files["index.md"] = _frontmatter({"type": "index", "title": pkg.package_id}) + "\n".join(index) + "\n"

    out_dir.mkdir(parents=True, exist_ok=True)
    for rel, content in files.items():
        (out_dir / rel).parent.mkdir(parents=True, exist_ok=True)
        (out_dir / rel).write_text(content)
    stats = {
        "path": "B", "package_id": pkg.package_id, "concepts": len(files),
        "extract_seconds": round(t_extract, 3), "build_seconds": round(time.perf_counter() - t0, 3),
        "storage_bytes": sum(f.stat().st_size for f in out_dir.rglob("*.md")),
    }
    (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
    return stats


class PathBBundle:
    def __init__(self, root: Path):
        self.root = root.resolve()

    def read(self, path: str) -> str:
        """Open a concept or index file; paths are relative to the bundle root and sandboxed to it."""
        target = (self.root / path.lstrip("/")).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError("path outside bundle")
        if target.is_dir():
            target = target / "index.md"
        if not target.exists() or target.suffix != ".md":
            raise FileNotFoundError(path)
        return target.read_text()

    def meta(self, path: str) -> dict:
        text = self.read(path)
        return yaml.safe_load(text.split("---")[1]) if text.startswith("---") else {}
