#!/usr/bin/env python
"""
Rebuild the ChromaDB collections from whatever is in the vault.

    voices          <- vault/writing/ and vault/inventory/process/
                       (your own writing: the register the agents write toward)
    miranda_papers  <- vault/theory/papers/, vault/theory/deposits/ and
                       vault/theory/reagan_arcs.md
                       (theory and research Miranda reaches into)

Out of the box the repo ships the process notes and reagan_arcs.md, so the
machine runs before you add anything. Add your own writing to vault/writing/
and papers you have the right to use to vault/theory/papers/, then run this again.

Reads .md, .txt, .pdf and .docx. Each run starts the two collections from
empty, so running it twice never duplicates anything. The 'faces' collection
is left alone (index_faces.py builds that).

Usage:
    python ingest.py
"""

import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import config

CHUNK_SIZE = 150   # words, as in the original indexers
OVERLAP    = 20
EXTENSIONS = {".md", ".txt", ".pdf", ".docx"}

SOURCES = {
    "voices": {
        "folders": [config.VAULT / "writing", config.VAULT / "inventory" / "process"],
        "tags": ["writing", "voice"],
        "description": "Rachel's writing. Opinion, commitment, the particular way she sees.",
    },
    "miranda_papers": {
        "folders": [config.VAULT / "theory" / "papers", config.VAULT / "theory" / "deposits",
                    config.VAULT / "theory" / "reagan_arcs.md"],
        "tags": ["theory", "miranda"],
        "description": "Theory, research, fragments, provocations. Strange, unresolved, resistant to reduction.",
    },
}


def read_text(path) -> str:
    suffix = path.suffix.lower()
    if suffix in (".md", ".txt"):
        return path.read_text(errors="ignore")
    if suffix == ".pdf":
        import fitz
        with fitz.open(str(path)) as doc:
            return "".join(page.get_text() for page in doc)
    if suffix == ".docx":
        from docx import Document
        return "\n".join(p.text for p in Document(str(path)).paragraphs)
    return ""


def chunk(text: str):
    words = text.split()
    step = CHUNK_SIZE - OVERLAP
    return [" ".join(words[i:i + CHUNK_SIZE]) for i in range(0, len(words), step)]


def main() -> None:
    import chromadb
    from rag import embedding_fn  # loads the local embedding model

    client = config.chroma_client()
    existing = {c.name if hasattr(c, "name") else c for c in client.list_collections()}

    for name, spec in SOURCES.items():
        if name in existing:
            client.delete_collection(name)
        coll = client.create_collection(
            name=name, embedding_function=embedding_fn,
            metadata={"description": spec["description"]},
        )

        files = sorted(
            f for folder in spec["folders"] if folder.exists()
            for f in ([folder] if folder.is_file() else folder.rglob("*"))
            if f.is_file() and f.suffix.lower() in EXTENSIONS
            and not f.name.startswith((".", "~$")) and f.name != "README.md"
        )
        total = 0
        for f in files:
            pieces = chunk(read_text(f))
            if not pieces:
                continue
            rel = str(f.relative_to(config.HOME)) if f.is_relative_to(config.HOME) else str(f)
            coll.add(
                documents=pieces,
                ids=[f"{rel}#{i}" for i in range(len(pieces))],
                metadatas=[{"source": f"{f.stem}_{i}", "provenance": rel,
                            "deposited": "ingest", "tags": ",".join(spec["tags"])}
                           for i in range(len(pieces))],
            )
            total += len(pieces)
            print(f"  {name}: {f.name} ({len(pieces)} chunks)")

        if not files:
            folders = ", ".join(str(p) for p in spec["folders"])
            print(f"  {name}: no files found in {folders}")
        print(f"{name}: {total} chunks\n")

    if not any(client.get_collection(n).count() for n in SOURCES):
        sys.exit("Both collections are empty. Add files to vault/writing/ and vault/theory/papers/, then run again.")


if __name__ == "__main__":
    main()
