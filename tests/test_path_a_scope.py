import numpy as np

from agent_on_duty.retrieval import path_a
from agent_on_duty.retrieval.path_a import Chunk, MultiIndex


class FakeIndex:
    def __init__(self, document: str, score: float):
        self.chunk = Chunk(chunk_id=0, document=document, page=1, text=document)
        self.score = score

    def search_scored(self, qvec, k):
        return [(self.score, self.chunk)]


def test_scope_separates_package_from_contracts(monkeypatch):
    monkeypatch.setattr(path_a, "_embed", lambda texts, prefix: np.zeros((1, 4), dtype="float32"))
    ix = MultiIndex([FakeIndex("RE-1.pdf", 0.2), FakeIndex("MSA.pdf", 0.9)])
    assert [c.document for c in ix.search("invoice")] == ["MSA.pdf", "RE-1.pdf"]
    assert [c.document for c in ix.search("invoice", scope="package")] == ["RE-1.pdf"]
    assert [c.document for c in ix.search("surcharge", scope="contract")] == ["MSA.pdf"]
