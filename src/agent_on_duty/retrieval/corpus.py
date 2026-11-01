"""Page-referenced text segments built from an ExtractedPackage — the common input of both pipelines."""

import re

from pydantic import BaseModel

from agent_on_duty.extraction.extract import ExtractedPackage

TOKEN_RE = re.compile(r"\w+|[^\w\s]")


def count_tokens(text: str) -> int:
    """Approximate token count (word pieces + punctuation); used for chunk sizing only.
    Context-token metrics come from Ollama's own prompt_eval_count."""
    return len(TOKEN_RE.findall(text))


class Segment(BaseModel):
    document: str
    doc_type: str
    page: int
    text: str


def segments(pkg: ExtractedPackage) -> list[Segment]:
    return [Segment(document=d.filename, doc_type=d.doc_type, page=p.page, text=p.text.strip())
            for d in pkg.documents for p in d.pages if p.text.strip()]
