"""The ingestion pipeline: put the Nest & Co customer handbook into Robin's content database.

This is the bottom row of the course slide "DocBot: from question to answer":

    1. Get the handbook       the 'production' version of the prompt robin/handbook in Langfuse
                              (or content/handbook.md if Langfuse can't be reached)
    2. Preprocess             tidy the text: line endings, trailing spaces, extra blank lines
    3. Chunk                  cut it into chunks: one per section (## heading)
    4. Embed                  turn every chunk into an embedding with OpenAI
    5. Store                  replace the old chunks in the content database (Postgres with pgvector)

It runs separately from Robin: start it under Actions > "Ingest the handbook" whenever the handbook
changes. Robin itself only searches the database. The run shows up in Langfuse as one trace,
"Ingestion – customer handbook", in the environment "ingestion".

Run it locally with:  python ingestion/ingest_handbook.py
It needs OPENAI_API_KEY and DATABASE_URL, and the Langfuse keys to read the handbook from Langfuse.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from dotenv import load_dotenv  # noqa: E402

load_dotenv()
os.environ.setdefault("LANGFUSE_TRACING_ENVIRONMENT", "ingestion")

from langfuse import get_client  # noqa: E402
from openai import OpenAI  # noqa: E402

import lookup  # noqa: E402
import prompts  # noqa: E402
import robin  # noqa: E402


def get_handbook() -> tuple[str, str]:
    """The handbook text and where it came from."""
    if os.getenv("LANGFUSE_PUBLIC_KEY"):
        robin.seed_prompts()  # creates robin/handbook from content/handbook.md if it isn't in Langfuse yet
        try:
            prompt = get_client().get_prompt("robin/handbook", label="production", cache_ttl_seconds=0)
            return prompt.prompt, f"Langfuse prompt robin/handbook, version {prompt.version}"
        except Exception as error:
            print(f"Could not read robin/handbook from Langfuse ({error}); using content/handbook.md")
    return prompts.HANDBOOK, "content/handbook.md in the repository"


def preprocess(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def main(client=None) -> int:
    client = client or OpenAI()
    langfuse = get_client()
    with langfuse.start_as_current_observation(as_type="chain", name="Ingestion – customer handbook") as run:
        with langfuse.start_as_current_observation(as_type="span", name="1. Get the handbook") as step:
            handbook, source = get_handbook()
            step.update(output=f"{len(handbook)} characters", metadata={"source": source})
        print(f"1. Got the handbook from {source}.")

        with langfuse.start_as_current_observation(as_type="span", name="2. Preprocess", input=handbook) as step:
            handbook = preprocess(handbook)
            code, version = lookup.document_info(handbook)
            step.update(output=handbook, metadata={"document_code": code, "document_version": version})
        print(f"2. Preprocessed {code}, version {version}.")

        with langfuse.start_as_current_observation(as_type="span", name="3. Chunk") as step:
            chunks = lookup.split_into_chunks(handbook)
            step.update(output=[{"chunk": n, "section": c.section, "characters": len(c.text), "text": c.text}
                                for n, c in enumerate(chunks, start=1)],
                        metadata={"rule": "one chunk per section (## heading)", "chunks": len(chunks)})
        print(f"3. Cut it into {len(chunks)} chunks: " + ", ".join(c.section for c in chunks) + ".")

        with langfuse.start_as_current_observation(as_type="embedding", name="4. Embed",
                                                   model=lookup.EMBEDDING_MODEL,
                                                   input=[c.section for c in chunks]) as step:
            embeddings, tokens = lookup.embed(client, [c.text for c in chunks])
            step.update(output=f"{len(embeddings)} embeddings of {len(embeddings[0])} numbers each",
                        usage_details={"input_tokens": tokens})
        print(f"4. Made {len(embeddings)} embeddings with {lookup.EMBEDDING_MODEL} ({tokens} tokens).")

        with langfuse.start_as_current_observation(as_type="span", name="5. Store in the content database") as step:
            stored = lookup.store(chunks, embeddings, code, version)
            step.update(output=f"{stored} chunks stored in the table {lookup.TABLE}",
                        metadata={"table": lookup.TABLE, "document_code": code, "document_version": version})
        print(f"5. Stored {stored} chunks in the table {lookup.TABLE}, replacing the previous version.")
        run.update(output=f"{code} version {version}: {stored} chunks in the content database")
    langfuse.flush()
    return stored


if __name__ == "__main__":
    main()
