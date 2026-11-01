"""Contract library: partner MSAs (and the buyer's purchasing guideline) are added once and reused.

A package then only needs PO, delivery note, goods receipt and invoice. Contracts are linked to a
package when one of their match terms (MSA number; buyer name for a guideline) appears on the
package's invoice or purchase order. Retrieval indexes are built once per contract and path, on first use.

    data/contracts/<id>/contract.json   metadata + match terms
    data/contracts/<id>/<original>.pdf  the document
    data/index/{A,B}/contracts/<id>/    Path A index / Path B concept files (built lazily)
"""

import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel

from agent_on_duty.extraction.extract import DocType, ExtractedDocument, extract_document, norm

from agent_on_duty.paths import CONTRACTS as LIBRARY
KINDS = {DocType.MSA: "msa", DocType.GUIDELINE: "guideline"}

COMPANY_RE = re.compile(r"([A-ZÄÖÜ][\wÄÖÜäöüß&.\-]+(?:\s+[A-ZÄÖÜ&][\wÄÖÜäöüß&.\-]+){0,3})\s+(GmbH(?:\s*&\s*Co\.\s*KG)?|AG|KG|SE|Ltd\.?|Inc\.?)\b")
CONTRACT_NO_RE = re.compile(r"(?:Contract|Agreement)\s+(?:No\.?|Number)\s*:?\s*([A-Z0-9][A-Z0-9./\-]{5,})", re.I)
DOCNO_RE = re.compile(r"\b[A-Z]{2,}(?:[-/][A-Z0-9]+){2,}\b")


class Contract(BaseModel):
    id: str
    kind: str  # "msa" | "guideline"
    filename: str
    title: str
    number: str | None = None
    parties: list[str] = []
    match_terms: list[str] = []
    pages: int = 0
    added_at: str = ""
    build: dict = {}  # per path: preparation stats (criterion 4)

    def pdf(self, library: Path = LIBRARY) -> Path:
        return library / self.id / self.filename


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:60]


def _squash(text: str) -> str:
    return re.sub(r"\s+", " ", norm(text)).strip().lower()


def detect(doc: ExtractedDocument) -> dict:
    """Contract number, parties and default match terms from the first pages."""
    head = " ".join(p.text for p in doc.pages[:2])
    flat = re.sub(r"\s+", " ", head)
    whole = re.sub(r"\s+", " ", " ".join(p.text for p in doc.pages)).lower()
    parties: list[str] = []
    for m in COMPANY_RE.finditer(flat):
        words = f"{m.group(1)} {m.group(2)}".split()
        # try the shortest trailing name first ("LF LORVATEN Fördertechnik GmbH" -> "Lorvaten Fördertechnik GmbH")
        for i in range(max(0, len(words) - 3), -1, -1)[::-1]:
            name = " ".join(words[i:])
            if len(name.split()) >= 2 and whole.count(name.lower()) >= 2:
                break
        else:
            name = " ".join(words)
        if name.lower() not in {p.lower() for p in parties}:
            parties.append(name)
    if doc.doc_type != DocType.MSA:  # guideline: the company it is about is named most often
        parties.sort(key=lambda n: -whole.count(n.lower()))
    number = None
    if doc.doc_type == DocType.MSA:
        m = CONTRACT_NO_RE.search(flat)
        number = m.group(1).rstrip(".,") if m else next((t for t in DOCNO_RE.findall(flat[:300]) if re.search(r"\d{4}", t)), None)
        terms = [number] if number else parties[1:2]
    else:
        terms = parties[:1]
    return {"number": number, "parties": parties[:4], "match_terms": [t for t in terms if t]}


def add(pdf: Path, filename: str | None = None, match_terms: list[str] | None = None,
        library: Path = LIBRARY) -> Contract:
    """Add an MSA or guideline PDF to the library (replaces an existing entry with the same file name)."""
    filename = Path(filename or pdf.name).name
    doc = extract_document(pdf)
    if doc.doc_type not in KINDS:
        raise ValueError(f"{filename} looks like a {doc.doc_type.value}, not a contract or guideline")
    found = detect(doc)
    cid = _slug(Path(filename).stem)
    target = library / cid
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    shutil.copy(pdf, target / filename)
    c = Contract(id=cid, kind=KINDS[doc.doc_type], filename=filename, title=doc.title or filename,
                 number=found["number"], parties=found["parties"],
                 match_terms=[t for t in (match_terms if match_terms is not None else found["match_terms"]) if t.strip()],
                 pages=len(doc.pages), added_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    save(c, library)
    return c


def save(c: Contract, library: Path = LIBRARY):
    (library / c.id / "contract.json").write_text(c.model_dump_json(indent=1))


def all_contracts(library: Path = LIBRARY) -> list[Contract]:
    if not library.exists():
        return []
    return [Contract.model_validate_json(f.read_text()) for f in sorted(library.glob("*/contract.json"))]


def get(cid: str, library: Path = LIBRARY) -> Contract | None:
    f = library / cid / "contract.json"
    return Contract.model_validate_json(f.read_text()) if f.exists() else None


def remove(cid: str, library: Path = LIBRARY, index_root: Path | None = None):
    shutil.rmtree(library / cid, ignore_errors=True)
    if index_root:
        for path in ("A", "B"):
            shutil.rmtree(index_root / path / "contracts" / cid, ignore_errors=True)


def matching(texts: list[str], library: Path = LIBRARY) -> list[Contract]:
    """Contracts whose match terms appear in the given texts (invoice, purchase order); at most one per kind."""
    hay = _squash(" ".join(texts))
    out: dict[str, Contract] = {}
    for c in all_contracts(library):
        if c.kind not in out and any(_squash(t) in hay for t in c.match_terms if t.strip()):
            out[c.kind] = c
    return list(out.values())


def find_file(filename: str, library: Path = LIBRARY) -> Path | None:
    for c in all_contracts(library):
        if c.filename == filename:
            return c.pdf(library)
    return None
