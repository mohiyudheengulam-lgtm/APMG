"""Path A — standard vector RAG (Exposé §5.2): 500-token chunks, 50 overlap, nomic-embed-text, FAISS top-5 by inner product."""

import json
import time
from pathlib import Path

import faiss
import numpy as np
import ollama
from pydantic import BaseModel

from agent_on_duty.extraction.extract import extract_package
from agent_on_duty.retrieval.corpus import TOKEN_RE, segments

EMBED_MODEL = "nomic-embed-text"
CHUNK_TOKENS, OVERLAP, TOP_K = 500, 50, 5


class Chunk(BaseModel):
    chunk_id: int
    document: str
    page: int
    text: str


def chunk_segment(text: str) -> list[str]:
    """Fixed-size token windows. Chunks never span pages so every chunk keeps a single page citation."""
    spans = [m.span() for m in TOKEN_RE.finditer(text)]
    if not spans:
        return []
    out, start = [], 0
    while True:
        end = min(start + CHUNK_TOKENS, len(spans))
        out.append(text[spans[start][0]:spans[end - 1][1]])
        if end == len(spans):
            return out
        start = end - OVERLAP


def _embed(texts: list[str], prefix: str) -> np.ndarray:
    vecs = np.array(ollama.embed(model=EMBED_MODEL, input=[prefix + t for t in texts]).embeddings, dtype="float32")
    faiss.normalize_L2(vecs)
    return vecs


class PathAIndex:
    def __init__(self, chunks: list[Chunk], index: faiss.Index):
        self.chunks, self.index = chunks, index

    @classmethod
    def build(cls, package_dir: Path, out_dir: Path, pkg=None, t_extract: float | None = None) -> dict:
        """Extract raw PDFs, chunk, embed, index. Returns preparation stats (criterion 4)."""
        t0 = time.perf_counter()
        if pkg is None:
            pkg = extract_package(package_dir)
            t_extract = time.perf_counter() - t0
        stats = cls.build_docs(pkg, out_dir, name=package_dir.name)
        stats["extract_seconds"] = round(t_extract or 0, 3)
        stats["build_seconds"] = round(stats["build_seconds"] + (t_extract or 0), 3)
        (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
        return stats

    @classmethod
    def build_docs(cls, pkg, out_dir: Path, name: str) -> dict:
        """Chunk, embed and index already extracted documents (a package, or one library contract)."""
        t0 = time.perf_counter()
        chunks = [Chunk(chunk_id=0, document=s.document, page=s.page, text=c)
                  for s in segments(pkg) for c in chunk_segment(s.text)]
        for i, c in enumerate(chunks):
            c.chunk_id = i
        vecs = _embed([c.text for c in chunks], "search_document: ")
        index = faiss.IndexFlatIP(vecs.shape[1])
        index.add(vecs)
        out_dir.mkdir(parents=True, exist_ok=True)
        faiss.write_index(index, str(out_dir / "index.faiss"))
        (out_dir / "chunks.json").write_text(json.dumps([c.model_dump() for c in chunks]))
        stats = {
            "path": "A", "package_id": name, "chunks": len(chunks), "extract_seconds": 0.0,
            "build_seconds": round(time.perf_counter() - t0, 3),
            "storage_bytes": sum(f.stat().st_size for f in out_dir.iterdir() if f.name != "build.json"),
            "documents": [{"file": d.filename, "type": d.doc_type.value} for d in pkg.documents],
        }
        (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
        return stats

    @classmethod
    def load(cls, out_dir: Path) -> "PathAIndex":
        chunks = [Chunk(**c) for c in json.loads((out_dir / "chunks.json").read_text())]
        return cls(chunks, faiss.read_index(str(out_dir / "index.faiss")))

    def search_scored(self, qvec: np.ndarray, k: int = TOP_K) -> list[tuple[float, Chunk]]:
        scores, ids = self.index.search(qvec, min(k, len(self.chunks)))
        return [(float(s), self.chunks[i]) for s, i in zip(scores[0], ids[0]) if i >= 0]

    def search(self, query: str, k: int = TOP_K) -> list[Chunk]:
        return [c for _, c in self.search_scored(_embed([query], "search_query: "), k)]


class MultiIndex:
    """A package index plus its linked contract indexes, searched as one: global top-k by inner product."""

    def __init__(self, indexes: list[PathAIndex]):
        self.indexes = indexes

    def search(self, query: str, k: int = TOP_K) -> list[Chunk]:
        qvec = _embed([query], "search_query: ")
        hits = [h for ix in self.indexes for h in ix.search_scored(qvec, k)]
        return [c for _, c in sorted(hits, key=lambda h: -h[0])[:k]]
