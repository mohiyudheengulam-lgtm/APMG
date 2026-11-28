"""Step-by-step demo of how a package becomes readable as OKF (Path B).

    uv run python scripts/okf_walkthrough.py PKG-011
    uv run python scripts/okf_walkthrough.py path/to/folder

No Ollama is needed. Upload is simulated by copying PDFs into a temporary package folder.
The demo calls the same extraction, self-check, contract-linking, and preparation functions
as the app. In the app, pipeline.prepare runs before the extraction self-check; this script
prints those stages in a teaching-friendly order, and prepare performs its own extraction.
"""

import shutil
import sys
import tempfile
from pathlib import Path

from agent_on_duty import pipeline
from agent_on_duty.agent.react import PathBTools
from agent_on_duty.extraction.check import check_package
from agent_on_duty.extraction.extract import DocType, extract_document, extract_package
from agent_on_duty.paths import PACKAGES
from agent_on_duty.retrieval.path_b import PathBBundle


def stage(n: int, title: str) -> None:
    print(f"\n{'=' * 78}\nSTAGE {n}: {title}\n{'=' * 78}")


def head(text: str, n: int = 14) -> str:
    lines = text.splitlines()
    return "\n".join(lines[:n]) + (f"\n... ({len(lines) - n} more lines)" if len(lines) > n else "")


def resolve_source(arg: str) -> Path:
    candidate = Path(arg).expanduser()
    src = candidate if candidate.is_dir() else PACKAGES / candidate
    if not src.is_dir():
        raise SystemExit(f"Package folder not found: {src}")
    if not any(src.glob("*.pdf")):
        raise SystemExit(f"No PDF files found in package folder: {src}")
    return src


def main(arg: str) -> None:
    src = resolve_source(arg)
    work = Path(tempfile.mkdtemp(prefix="okf_walkthrough_"))

    stage(1, "UPLOAD SIMULATION: copy the PDFs into a temporary package folder")
    pkg_dir = work / "uploads" / src.name
    pkg_dir.mkdir(parents=True)
    for pdf in sorted(src.glob("*.pdf")):
        shutil.copy2(pdf, pkg_dir / pdf.name)
        print(f"  stored {pdf.name}")

    stage(2, "EXTRACTION: classify each PDF and extract its records")
    for pdf in sorted(pkg_dir.glob("*.pdf")):
        d = extract_document(pdf)
        print(f"\n  {d.filename}")
        print(f"    type = {d.doc_type.value}   title = {d.title!r}   pages = {[p.page for p in d.pages]}   "
              f"ocr = {any(p.ocr for p in d.pages)}")
        if d.record:
            r = d.record
            print(f"    record = {type(r).__name__}: "
                  + ", ".join(f"{k}={v!r}" for k, v in r.model_dump(exclude={"lines", "surcharges", "source"}).items()))
            for ln in r.lines:
                print(f"      line {ln.item_no:<14} qty={ln.quantity} price={ln.unit_price} total={ln.line_total}")
            for surcharge in getattr(r, "surcharges", []):
                print(f"      surcharge {surcharge.label!r} = {surcharge.amount}")

    pkg = extract_package(pkg_dir)
    stage(3, "SELF-CHECK: do extracted numbers reproduce the totals printed on the documents?")
    check = check_package(pkg, pkg_dir)
    print(f"  status = {check.status}")
    for c in check.checks:
        print(f"    [{'ok' if c.ok else '!!'}] {c.document}: {c.name} {c.detail}")

    stage(4, "CONTRACT LINKING: which library contracts does this package refer to?")
    linked = pipeline.linked_contracts(pkg)
    for c in linked:
        print(f"  {c.kind:<9} {c.id}  (matched on {c.match_terms})")
    if not linked:
        print("  none (library empty, or no match term appears on the invoice / PO)")
    print(f"  package itself contains: {[d.doc_type.value for d in pkg.documents]}")

    stage(5, "CONVERSION: pipeline.prepare writes the OKF bundle and links library contracts")
    index_root = work / "index"
    stats = pipeline.prepare(pkg_dir, "B", index_root)
    bundle_dir = index_root / "B" / pkg_dir.name
    print(f"  concepts = {stats['concepts']}   build = {stats['build_seconds']}s   "
          f"linked contracts = {stats['contracts']}")
    print("\n  bundle on disk:")
    for f in sorted(bundle_dir.rglob("*")):
        if f.is_file():
            print(f"    {f.relative_to(bundle_dir)}  ({f.stat().st_size} bytes)")
    for cid in stats["contracts"]:
        cdir = index_root / "B" / "contracts" / cid
        files = sorted(cdir.rglob("*.md"))
        print(f"\n  library bundle {cid}: {len(files)} concept files (built once, shared by packages)")

    stage(6, "WHAT THE FILES LOOK LIKE")
    for rel in ("index.md", "invoice.md"):
        path = bundle_dir / rel
        if path.is_file():
            print(f"\n--- {rel} ---\n{path.read_text(encoding='utf-8')}")
        elif rel == "invoice.md":
            print("\n--- invoice.md ---\n(no invoice concept was generated)")

    msa_index = bundle_dir / "msa" / "index.md"
    if not msa_index.is_file():
        msa_index = next(
            (index_root / "B" / "contracts" / cid / "msa" / "index.md"
             for cid in stats["contracts"]
             if (index_root / "B" / "contracts" / cid / "msa" / "index.md").is_file()),
            None,
        )
    if msa_index:
        print(f"\n--- {msa_index.relative_to(index_root / 'B')} ---")
        print(head(msa_index.read_text(encoding="utf-8"), 16))
        surcharge_file = next(
            (f for f in msa_index.parent.glob("*.md")
             if f.name != "index.md" and "surcharge" in f.name.lower()),
            None,
        )
        if surcharge_file:
            print(f"\n--- {surcharge_file.relative_to(index_root / 'B')} ---")
            print(head(surcharge_file.read_text(encoding="utf-8"), 16))
        else:
            print("\n  no surcharge-named MSA section was found")
    else:
        print("\n  no MSA bundle is present")

    stage(7, "NAVIGATION: what the agent's read tool returns and records as seen")
    msa_dir = next(
        (index_root / "B" / "contracts" / cid / "msa"
         for cid in stats["contracts"]
         if (index_root / "B" / "contracts" / cid / "msa").is_dir()),
        None,
    )
    mounts = {"msa": msa_dir} if msa_dir else {}
    bundle = PathBBundle(bundle_dir, mounts=mounts)
    tools = PathBTools(bundle)
    invoice = pkg.get(DocType.INVOICE)
    calls = [["index.md"]]
    if invoice and (bundle_dir / "invoice.md").is_file():
        if msa_index:
            calls.append(["invoice.md", "msa/index.md"])
        calls.append([invoice.filename])

    for paths in calls:
        args = {"paths": paths} if len(paths) > 1 else {"path": paths[0]}
        text, seen = tools.call("read", args)
        print(f"\n  read({paths})  ->  {len(text)} characters")
        print(f"    evidence recorded (document, page): {sorted(seen)}")

    for bad in ("../../etc/passwd", "does_not_exist.md"):
        try:
            bundle.read(bad)
        except (ValueError, FileNotFoundError) as e:
            print(f"\n  read({bad!r})  ->  {type(e).__name__}: {str(e)[:90]}")
    print(f"\nWork folder (inspect the bundle yourself): {work}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "PKG-011")
