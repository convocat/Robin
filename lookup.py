"""Robin's look-up (RAG): the content database and the search in it.

The steps follow the course slide "DocBot: from question to answer":

    Ingestion pipeline    ingestion/ingest_handbook.py: get the handbook, preprocess it, cut it into
                          chunks, turn each chunk into an embedding, and store it all in the content
                          database (Postgres with pgvector). It runs separately from Robin, whenever
                          the handbook changes: Actions > "Ingest the handbook".
    Question recognition  robin.py: a small model rewrites the customer's message into a search query
    Information retrieval search() below: the query becomes an embedding, and the database returns the
                          chunks whose embeddings are closest to it
    Response generation   robin.py: Robin answers with those chunks as its context

Robin never reads the handbook itself: it only queries the database.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
TABLE = "handbook_chunks"
MAX_RESULTS_CHOICES = (1, 3, 5)
DEFAULT_MAX_RESULTS = 3

SCHEMA = f"""
CREATE EXTENSION IF NOT EXISTS vector;
CREATE TABLE IF NOT EXISTS {TABLE} (
    id               serial PRIMARY KEY,
    document_code    text NOT NULL,
    document_version text NOT NULL,
    chunk_number     integer NOT NULL,
    section          text NOT NULL,
    content          text NOT NULL,
    embedding        vector NOT NULL,
    embedding_model  text NOT NULL,
    ingested_at      timestamptz NOT NULL DEFAULT now()
);
"""


class LookUpError(Exception):
    """The look-up can't run: no database, or nothing ingested yet."""


@dataclass
class Chunk:
    section: str      # the heading, for example "Delivery"
    text: str         # the heading plus everything under it


@dataclass
class Hit:
    section: str
    text: str
    similarity: float  # 1 means the same meaning, 0 means unrelated
    document_version: str
    ingested_at: str


# ---------------------------------------------------------------------------
# Chunking (used by the ingestion pipeline)
# ---------------------------------------------------------------------------

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


def document_info(handbook: str) -> tuple[str, str]:
    """The document code and version from the handbook's metadata table."""
    def field(name: str, default: str) -> str:
        match = re.search(rf"\*\*{name}\*\*\s*\|\s*([^|\n]+)", handbook)
        return match.group(1).strip() if match else default
    return field("Document code", "unknown"), field("Version", "unknown")


# ---------------------------------------------------------------------------
# Embeddings and the database
# ---------------------------------------------------------------------------

def embed(client, texts: list[str]) -> tuple[list[list[float]], int]:
    """Turn texts into embeddings. Returns the embeddings and the number of tokens used."""
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    usage = getattr(response, "usage", None)
    return [item.embedding for item in response.data], getattr(usage, "total_tokens", 0) or 0


def as_vector(embedding: list[float]) -> str:
    """pgvector's text format: [0.1,0.2,...]"""
    return "[" + ",".join(f"{x:.8f}" for x in embedding) + "]"


def connect():
    url = os.getenv("DATABASE_URL", "")
    if not url:
        raise LookUpError("No content database: the environment variable DATABASE_URL is not set.")
    import psycopg  # only needed when the look-up is used

    return psycopg.connect(url, connect_timeout=5)


def store(chunks: list[Chunk], embeddings: list[list[float]], document_code: str, document_version: str) -> int:
    """Replace the handbook's chunks in the database with these ones, in one transaction."""
    with connect() as conn, conn.transaction():
        conn.execute(SCHEMA)
        conn.execute(f"DELETE FROM {TABLE} WHERE document_code = %s", (document_code,))
        for number, (chunk, embedding) in enumerate(zip(chunks, embeddings), start=1):
            conn.execute(
                f"INSERT INTO {TABLE} (document_code, document_version, chunk_number, section, content, "
                f"embedding, embedding_model) VALUES (%s, %s, %s, %s, %s, %s::vector, %s)",
                (document_code, document_version, number, chunk.section, chunk.text, as_vector(embedding),
                 EMBEDDING_MODEL),
            )
    return len(chunks)


def search(query_embedding: list[float], limit: int) -> list[Hit]:
    """The chunks closest in meaning to the query (cosine distance, `<=>` in pgvector)."""
    vector = as_vector(query_embedding)
    try:
        with connect() as conn:
            rows = conn.execute(
                f"SELECT section, content, 1 - (embedding <=> %s::vector) AS similarity, document_version, "
                f"ingested_at FROM {TABLE} ORDER BY embedding <=> %s::vector LIMIT %s",
                (vector, vector, limit),
            ).fetchall()
    except LookUpError:
        raise
    except Exception as error:
        if "does not exist" in str(error):
            raise LookUpError("The content database is empty: run the ingestion first "
                              "(Actions > \"Ingest the handbook\").") from error
        raise
    if not rows:
        raise LookUpError("The content database is empty: run the ingestion first "
                          "(Actions > \"Ingest the handbook\").")
    return [Hit(section, content, float(similarity), version, str(ingested_at))
            for section, content, similarity, version, ingested_at in rows]


# ---------------------------------------------------------------------------
# Settings and formatting (used by Robin)
# ---------------------------------------------------------------------------

def max_results(value) -> int:
    """The number of chunks to look up: 1, 3 or 5. Anything else becomes the default."""
    try:
        number = int(value)
    except (TypeError, ValueError):
        return DEFAULT_MAX_RESULTS
    return number if number in MAX_RESULTS_CHOICES else DEFAULT_MAX_RESULTS


def format_sources(hits: list[Hit]) -> str:
    """The chunks as Robin sees them in its system prompt."""
    if not hits:
        return "(No sections were found.)"
    return "\n\n".join(f"### Section: {hit.section}\n{_without_heading(hit.text)}" for hit in hits)


def _without_heading(text: str) -> str:
    return re.sub(r"^## .*\n?", "", text, count=1).strip()
