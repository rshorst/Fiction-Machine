#!/usr/bin/env python3
"""
Regenerate vault/inventory/corpus.md from live ChromaDB state.
Uses sqlite3 directly — no sentence-transformers needed.
Run from the repo folder.
"""

import sqlite3
import os
from pathlib import Path
from datetime import datetime

import config

DB        = config.CHROMA_DIR / "chroma.sqlite3"
INVENTORY = config.VAULT / "inventory" / "corpus.md"


def _query_counts(cur):
    cur.execute("""
        SELECT c.name, COUNT(e.id)
        FROM collections c
        JOIN segments s ON s.collection = c.id
        JOIN embeddings e ON e.segment_id = s.id
        GROUP BY c.name
    """)
    return {row[0]: row[1] for row in cur.fetchall()}


def _most_recent_deposited(cur, collection_name):
    cur.execute("""
        SELECT MAX(em.string_value)
        FROM collections c
        JOIN segments s ON s.collection = c.id
        JOIN embeddings e ON e.segment_id = s.id
        JOIN embedding_metadata em ON em.id = e.id
        WHERE c.name = ? AND em.key = 'deposited'
    """, (collection_name,))
    row = cur.fetchone()
    if row and row[0]:
        return row[0][:10]
    return None


def _most_recent_faces_mtime(cur):
    cur.execute("""
        SELECT em.string_value
        FROM collections c
        JOIN segments s ON s.collection = c.id
        JOIN embeddings e ON e.segment_id = s.id
        JOIN embedding_metadata em ON em.id = e.id
        WHERE c.name = 'faces' AND em.key = 'local_path'
    """)
    mtimes = []
    for (path,) in cur.fetchall():
        try:
            mtimes.append(os.path.getmtime(path))
        except OSError:
            pass
    if mtimes:
        return datetime.fromtimestamp(max(mtimes)).strftime("%Y-%m-%d")
    return None


TEMPLATE = """\
# Corpus inventory

What is indexed in ChromaDB, and what is not.

## Collections

### voices
Rachel's writing — essays, academic papers, Substack posts. Indexed from vault/writing/.
{voices_count:,} chunks
Last indexed: {voices_date}
Used by: Richard (register calibration during draft writing and revision), Sue Pen (annotation passes).

### miranda_papers
Theory deposits accumulated across all narratives. Each deposit tagged with its source slug.
{mp_count:,} documents
Last updated: {mp_date}
Used by: Miranda (queries existing corpus before reaching the web), Richard (at plot generation via ReachMirandaTool).

### faces
Portrait photographs from vault/faces/.
{faces_count:,} entries
Last updated: {faces_date}
Used by: Frances (face fetch during character building).

## Excluded from indexing

The following directories are not indexed into any ChromaDB collection:

- vault/inventory/ — design decisions and preference signals. If indexed, judgments about specific drafts would become substrate for future generation. The propagation risk is documented in build-notes/2026-04-26_architecture-and-propagation.md.
- vault/stories/[slug]/ — produced narratives and their run artifacts. Outputs, not corpus.
"""


def main():
    if not DB.exists():
        print(f"ChromaDB not found at {DB}")
        return

    conn = sqlite3.connect(DB)
    cur  = conn.cursor()

    counts      = _query_counts(cur)
    voices_date = _most_recent_deposited(cur, "voices") or "unknown"
    mp_date     = _most_recent_deposited(cur, "miranda_papers") or "unknown"
    faces_date  = _most_recent_faces_mtime(cur) or "unknown"
    conn.close()

    new_content = TEMPLATE.format(
        voices_count = counts.get("voices", 0),
        voices_date  = voices_date,
        mp_count     = counts.get("miranda_papers", 0),
        mp_date      = mp_date,
        faces_count  = counts.get("faces", 0),
        faces_date   = faces_date,
    )

    old_content = INVENTORY.read_text() if INVENTORY.exists() else ""

    if new_content == old_content:
        print("corpus.md is already up to date.")
        return

    old_lines = set(old_content.splitlines())
    new_lines = set(new_content.splitlines())
    for line in sorted(old_lines - new_lines):
        if line.strip():
            print(f"- {line}")
    for line in sorted(new_lines - old_lines):
        if line.strip():
            print(f"+ {line}")

    INVENTORY.write_text(new_content)
    print(f"\nWritten to {INVENTORY}")


if __name__ == "__main__":
    main()
