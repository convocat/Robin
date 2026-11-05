"""Robin's look-up: find the handbook sections that answer a customer's question (RAG).

The steps follow the course slide "DocBot: from question to answer":

    Ingestion             the handbook is cut into chunks (one per section) and each chunk is turned
                          into an embedding: a list of numbers that captures its meaning
    Question recognition  a small model rewrites the customer's message into a search query
    Information retrieval the query becomes an embedding too, and the closest chunks are picked
    Response generation   Robin answers with those chunks as its context (see robin.py)

The handbook is small, so there's no separate database: the chunks and their embeddings are kept
in memory, and made again whenever the handbook text changes (for example a new version in Langfuse).
"""

from __future__ import annotations

import hashlib
import math
import os
import re
from dataclasses import dataclass

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
MAX_RESULTS_CHOICES = (1, 3, 5)
DEFAULT_MAX_RESULTS = 3


@dataclass
class Chunk:
    section: str      # the heading, for example "Delivery"
    text: str         # the heading plus everything under it
    embedding: list[float] | None = None


def split_into_chunks(handbook: str) -> list[Chunk]:
    """One chunk per '## ' section. The title and document information before the first section
    become a chunk of their own, called 'Document information'."""
    chunks: list[Chunk] = []
    section, lines = "Document information", []
    for line in handbook.splitlines():
        if line.startswith("## "):
            if "".join(lines).strip():
                chunks.append(Chunk(section, "\n".join(lines).strip()))
            section, lines = line[3:].strip(), [line]
        else:
            lines.append(line)
    if "".join(lines).strip():
        chunks.append(Chunk(section, "\n".join(lines).strip()))
    return chunks


def max_results(value) -> int:
    """The number of chunks to look up: 1, 3 or 5. Anything else becomes the default."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_RESULTS
    return number if number in MAX_RESULTS_CHOICES else DEFAULT_MAX_RESULTS


def embed(client, texts: list[str]) -> tuple[list[list[float]], int]:
    """Turn texts into embeddings. Returns the embeddings and the number of tokens used."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    usage = getattr(response, "usage", None)
    return [item.embedding for item in response.data], getattr(usage, "total_tokens", 0) or 0


def similarity(a: list[float], b: list[float]) -> float:
    """Cosine similarity: 1 means the same meaning, 0 means unrelated."""
    dot = sum(x * y for x, y in zip(a, b))
    norm = math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b))
    return dot / norm if norm else 0.0


class Index:
    """The handbook's chunks with their embeddings, made once per handbook version."""

    def __init__(self):
        self._key: str | None = None
        self.chunks: list[Chunk] = []

    def ensure(self, client, handbook: str) -> bool:
        """Make the chunks and embeddings if the handbook changed. Returns True if it did that now."""
        key = hashlib.sha256(f"{EMBEDDING_MODEL}\n{handbook}".encode()).hexdigest()
        if key != self._key:
            chunks = split_into_chunks(handbook)
            embeddings, _ = embed(client, [chunk.text for chunk in chunks])
            for chunk, vector in zip(chunks, embeddings):
                chunk.embedding = vector
            self.chunks, self._key = chunks, key
            return True
        return False

    def search(self, query_embedding: list[float], limit: int) -> list[tuple[Chunk, float]]:
        scored = [(chunk, similarity(query_embedding, chunk.embedding)) for chunk in self.chunks]
        scored.sort(key=lambda pair: pair[1], reverse=True)
        return scored[:limit]


INDEX = Index()


def format_sources(found: list[tuple[Chunk, float]]) -> str:
    """The chunks as Robin sees them in its system prompt."""
    if not found:
        return "(No sections were found.)"
    return "\n\n".join(f"### Section: {chunk.section}\n{_without_heading(chunk.text)}" for chunk, _ in found)


def _without_heading(text: str) -> str:
    return re.sub(r"^## .*\n?", "", text, count=1).strip()
