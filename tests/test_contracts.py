"""Contract library: detection, linking packages to their MSA and guideline, adding a new MSA."""

import json
import shutil

import pytest

from agent_on_duty import contracts, pipeline
from agent_on_duty.extraction.extract import extract_package


def test_library_holds_seed_contracts(library):
    cs = contracts.all_contracts(library)
    assert sorted(c.kind for c in cs) == ["guideline", "guideline", "msa", "msa"]
    numbers = {c.number for c in cs if c.kind == "msa"}
    assert numbers == {"MSA-LFT-PKV-2026-01", "RV-QE-SC/2026/003"}


def test_every_package_links_its_own_contracts(packages, library):
    for pdir in packages:
        gt = json.loads((pdir / "ground_truth.json").read_text())
        linked = {c.kind: c.filename for c in pipeline.linked_contracts(extract_package(pdir), library)}
        assert linked == {"msa": gt["contract_documents"]["msa"], "guideline": gt["contract_documents"]["purchasing_guideline"]}, pdir.name


def test_package_bundle_mounts_library_msa(packages, library, tmp_path):
    pdir = packages[0]
    pipeline.prepare(pdir, "B", tmp_path, lib=library)
    tools = pipeline.retrieval_for(pdir, "B", tmp_path, lib=library)
    text, seen = tools.call("read", {"paths": ["index.md", "msa/index.md", "guideline.md"]})
    assert "contract library" in text and "Master agreement" in text
    assert any(doc.endswith(".pdf") for doc, _ in seen)
    assert (tmp_path / "B" / "contracts").exists()  # contract built once, outside the package bundle


def test_add_new_msa_and_reject_non_contracts(packages, library, tmp_path):
    lib = tmp_path / "lib"
    src = contracts.find_file("RV-QE-SC-2026-003.pdf", library)
    c = contracts.add(src, filename="NEW-SUPPLIER-MSA.pdf", library=lib)
    assert c.kind == "msa" and c.match_terms == ["RV-QE-SC/2026/003"]
    assert [x.id for x in contracts.all_contracts(lib)] == [c.id]
    invoice = next(p for p in packages[-1].glob("IN*.pdf"))
    with pytest.raises(ValueError, match="not a contract"):
        contracts.add(invoice, library=lib)
    contracts.remove(c.id, library=lib)
    assert contracts.all_contracts(lib) == []
