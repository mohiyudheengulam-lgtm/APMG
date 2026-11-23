"""Path A must not crash on a package with no readable text (e.g. scanned PDFs). No Ollama needed."""
 
import numpy as np
import pytest
 
from agent_on_duty.extraction.extract import DocType, ExtractedDocument, ExtractedPackage, PageText
from agent_on_duty.retrieval import path_a
from agent_on_duty.retrieval.path_a import Chunk, MultiIndex, PathAIndex
 
 
@pytest.fixture
def no_ollama(monkeypatch):
    """Fail loudly if anything tries to call Ollama."""
    def boom(*args, **kwargs):
        raise AssertionError("Ollama must not be called for an empty package")
    monkeypatch.setattr(path_a.ollama, "embed", boom)
 
 
def empty_package() -> ExtractedPackage:
    doc = ExtractedDocument(filename="INV-scan.pdf", doc_type=DocType.INVOICE,
                            pages=[PageText(page=1, text=""), PageText(page=2, text="   \n ")])
    return ExtractedPackage(package_id="pkg-empty", documents=[doc])
 
 
def test_empty_package_builds_empty_index(tmp_path, no_ollama):
    stats = PathAIndex.build_docs(empty_package(), tmp_path, name="pkg-empty")
    assert stats["chunks"] == 0
    assert "pkg-empty" in stats["warning"]
    assert (tmp_path / "index.faiss").exists() and (tmp_path / "chunks.json").exists()
 
    index = PathAIndex.load(tmp_path)
    assert index.chunks == []
    assert index.search("unit price of item 10") == []
    assert index.search_scored(np.zeros((1, path_a.EMBED_DIM), dtype="float32")) == []
    assert MultiIndex([index]).search("unit price of item 10") == []
 
 
def test_empty_index_next_to_full_one(tmp_path, monkeypatch):
    """An empty package index must not break search over a linked contract that does have text."""
    PathAIndex.build_docs(empty_package(), tmp_path / "pkg", name="pkg-empty")
    empty = PathAIndex.load(tmp_path / "pkg")
 
    vec = np.zeros((1, path_a.EMBED_DIM), dtype="float32")
    vec[0, 0] = 1.0
    full = PathAIndex([Chunk(chunk_id=0, document="MSA.pdf", page=3, text="Prices are fixed.")],
                      path_a.faiss.IndexFlatIP(path_a.EMBED_DIM))
    full.index.add(vec)
    monkeypatch.setattr(path_a, "_embed", lambda texts, prefix: vec)
 
    hits = MultiIndex([empty, full]).search("price")
    assert [(c.document, c.page) for c in hits] == [("MSA.pdf", 3)]
 
