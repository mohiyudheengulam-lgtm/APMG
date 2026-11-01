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
    def build(cls, package_dir: Path, out_dir: Path) -> dict:
        """Extract raw PDFs, chunk, embed, index. Returns preparation stats (criterion 4)."""
        t0 = time.perf_counter()
        pkg = extract_package(package_dir)
        t_extract = time.perf_counter() - t0
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
            "path": "A", "package_id": package_dir.name, "chunks": len(chunks),
            "extract_seconds": round(t_extract, 3), "build_seconds": round(time.perf_counter() - t0, 3),
            "storage_bytes": sum(f.stat().st_size for f in out_dir.iterdir() if f.name != "build.json"),
            "documents": [{"file": d.filename, "type": d.doc_type.value} for d in pkg.documents],
        }
        (out_dir / "build.json").write_text(json.dumps(stats, indent=1))
        return stats

    @classmethod
    def load(cls, out_dir: Path) -> "PathAIndex":
        chunks = [Chunk(**c) for c in json.loads((out_dir / "chunks.json").read_text())]
        return cls(chunks, faiss.read_index(str(out_dir / "index.faiss")))

    def search(self, query: str, k: int = TOP_K) -> list[Chunk]:
        scores, ids = self.index.search(_embed([query], "search_query: "), min(k, len(self.chunks)))
        return [self.chunks[i] for i in ids[0] if i >= 0]
