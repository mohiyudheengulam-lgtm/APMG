"""End-to-end pipeline per retrieval path: raw PDFs → (own extraction + index/bundle) → agent → PENDING_REVIEW.

Contracts (MSA, purchasing guideline) come from the contract library when the package does not contain them;
their indexes are built once per contract and reused by every package that links to them.
"""

import json
import time
from pathlib import Path

from agent_on_duty import contracts as library
from agent_on_duty.agent.react import AgentRun, PathATools, PathBTools, Verifier
from agent_on_duty.audit.store import RecommendationWriter
from agent_on_duty.extraction.extract import DocType, ExtractedPackage, extract_document, extract_package
from agent_on_duty.retrieval import path_b
from agent_on_duty.retrieval.path_a import MultiIndex, PathAIndex
from agent_on_duty.retrieval.path_b import PathBBundle

CONTRACT_TYPES = {"msa": DocType.MSA, "guideline": DocType.GUIDELINE}


def linked_contracts(pkg: ExtractedPackage, lib: Path = library.LIBRARY) -> list[library.Contract]:
    """Library contracts referenced on the invoice / PO, for the contract kinds the package does not contain itself."""
    texts = [p.text for d in pkg.documents if d.doc_type in (DocType.INVOICE, DocType.PURCHASE_ORDER) for p in d.pages]
    return [c for c in library.matching(texts, lib) if pkg.get(CONTRACT_TYPES[c.kind]) is None]


def contract_index(c: library.Contract, path: str, index_root: Path, lib: Path = library.LIBRARY) -> Path:
    """Build (once) and return the contract's Path A index / Path B concept folder."""
    out = index_root / path / "contracts" / c.id
    if not (out / "build.json").exists():
        t0 = time.perf_counter()
        doc = extract_document(c.pdf(lib))
        t_extract = time.perf_counter() - t0
        pkg = ExtractedPackage(package_id=c.id, documents=[doc])
        stats = PathAIndex.build_docs(pkg, out, name=c.id) if path == "A" else path_b.convert_contract(doc, out)
        stats["extract_seconds"] = round(t_extract, 3)
        stats["build_seconds"] = round(stats["build_seconds"] + t_extract, 3)
        (out / "build.json").write_text(json.dumps(stats, indent=1))
        c.build[path] = stats
        library.save(c, lib)
    return out


def _mounts(cs: list[library.Contract], index_root: Path, lib: Path) -> dict[str, Path]:
    mounts = {}
    for c in cs:
        root = contract_index(c, "B", index_root, lib)
        if c.kind == "msa":
            mounts["msa"] = root / "msa"
        else:
            mounts["guideline.md"] = root / "guideline.md"
    return mounts


def prepare(package_dir: Path, path: str, index_root: Path, rebuild: bool = False, lib: Path = library.LIBRARY) -> dict:
    """Build the package's Path A index or Path B bundle (each path runs its own extraction) and link library
    contracts. Cached; rebuilt when the set of linked contracts changes."""
    out = index_root / path / package_dir.name
    cached = json.loads((out / "build.json").read_text()) if (out / "build.json").exists() and not rebuild else None
    t0 = time.perf_counter()
    pkg = extract_package(package_dir)
    t_extract = time.perf_counter() - t0
    cs = linked_contracts(pkg, lib)
    ids = sorted(c.id for c in cs)
    if cached and cached.get("contracts", []) == ids:
        return cached
    if path == "A":
        for c in cs:
            contract_index(c, "A", index_root, lib)
        stats = PathAIndex.build(package_dir, out, pkg=pkg, t_extract=t_extract)
    else:
        stats = path_b.convert(package_dir, out, pkg=pkg, t_extract=t_extract, mounts=_mounts(cs, index_root, lib))
    stats["contracts"] = ids
    stats["documents"] = stats["documents"] + [{"file": c.filename, "type": c.kind, "library": True} for c in cs]
    (out / "build.json").write_text(json.dumps(stats, indent=1))
    return stats


def retrieval_for(package_dir: Path, path: str, index_root: Path, lib: Path = library.LIBRARY) -> PathATools | PathBTools:
    out = index_root / path / package_dir.name
    build = json.loads((out / "build.json").read_text())
    cs = [c for c in (library.get(cid, lib) for cid in build.get("contracts", [])) if c]
    if path == "A":
        indexes = [PathAIndex.load(out)] + [PathAIndex.load(contract_index(c, "A", index_root, lib)) for c in cs]
        return PathATools(MultiIndex(indexes))
    return PathBTools(PathBBundle(out, mounts=_mounts(cs, index_root, lib)))


def verify(package_dir: Path, path: str, index_root: Path, writer: RecommendationWriter | None = None,
           extra: dict | None = None, on_step=None, assisted: bool = False,
           lib: Path = library.LIBRARY) -> tuple[AgentRun, str | None]:
    """assisted=True pre-submits the documents from extraction (fast mode for real use; never used by the benchmark)."""
    build = prepare(package_dir, path, index_root, lib=lib)
    run = Verifier(package_dir.name, retrieval_for(package_dir, path, index_root, lib), documents=build.get("documents"),
                   assisted=extract_package(package_dir) if assisted else None).verify(on_step=on_step)
    vid = writer.save(run, (extra or {}) | {"build": build}) if writer else None
    return run, vid
