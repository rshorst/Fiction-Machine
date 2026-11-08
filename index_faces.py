"""
index_faces.py  (stage 2 of 2)

Reads the images folder, looks each survivor up in the manifest, and builds
the Chroma 'faces' collection alongside 'voices' and 'miranda_papers' in
the main chromadb/ database. The filesystem is the source of truth.

Usage:
    python index_faces.py

Inputs:
    <repo>/faces/images/        — face JPGs
    <repo>/faces/manifest.json  — written by pull_faces.py

Outputs:
    <repo>/chromadb/            — Chroma 'faces' collection (joins voices, miranda_papers)
    <repo>/faces/manifest_indexed.json — record of what got indexed
"""

import json
import sys
from pathlib import Path

import chromadb

# Use rag.py's embedding function directly, so the faces collection sits in
# the database in exactly the same shape as voices and miranda_papers.
sys.path.insert(0, str(Path(__file__).parent))
from rag import embedding_fn  # type: ignore  # noqa: E402


import config  # noqa: E402

FACES_DIR = config.FACES_DIR
IMAGES_DIR = FACES_DIR / "images"
MANIFEST_PATH = FACES_DIR / "manifest.json"
INDEXED_PATH = FACES_DIR / "manifest_indexed.json"
# Same Chroma folder as rag.py, from config.py.
CHROMA_DIR = config.CHROMA_DIR


def document_text(rec: dict) -> str:
    """Body Chroma embeds — photographer's own language, plus tags + query."""
    parts = [
        rec.get("description", ""),
        rec.get("alt_description", ""),
        ", ".join(rec.get("tags", [])),
        f"(query: {rec.get('query', '')})",
    ]
    return " | ".join(p for p in parts if p) or rec.get("query", "untitled")


def main() -> None:
    if not MANIFEST_PATH.exists():
        raise SystemExit(f"No manifest at {MANIFEST_PATH}. Run pull_faces.py first.")
    if not IMAGES_DIR.exists():
        raise SystemExit(f"No images folder at {IMAGES_DIR}.")

    manifest = {rec["id"]: rec for rec in json.loads(MANIFEST_PATH.read_text())}
    print(f"Manifest has {len(manifest)} records.")

    survivor_ids = {p.stem for p in IMAGES_DIR.glob("*.jpg")}
    print(f"Folder has {len(survivor_ids)} images.")

    survivors = [manifest[i] for i in survivor_ids if i in manifest]
    orphans = survivor_ids - set(manifest.keys())
    if orphans:
        print(f"  ! {len(orphans)} images have no manifest entry — skipped.")

    cut = set(manifest.keys()) - survivor_ids
    print(f"Pruned: {len(cut)} faces removed since pull.")
    print(f"Indexing: {len(survivors)} faces into {CHROMA_DIR}\n")

    if not survivors:
        raise SystemExit("Nothing to index.")

    client = config.chroma_client()

    # Reset so collection always mirrors current folder
    try:
        client.delete_collection("faces")
        print("Cleared existing 'faces' collection.")
    except Exception:
        pass

    coll = client.create_collection(
        name="faces",
        embedding_function=embedding_fn,
        metadata={"description": "Frances's face pool — Unsplash portraits, curated"},
    )

    ids, docs, metas = [], [], []
    for rec in survivors:
        ids.append(rec["id"])
        docs.append(document_text(rec))
        metas.append({
            "query": rec.get("query", ""),
            "photographer": rec.get("photographer", ""),
            "photographer_username": rec.get("photographer_username", ""),
            "unsplash_url": rec.get("unsplash_url", ""),
            "local_path": rec.get("local_path", str(IMAGES_DIR / f"{rec['id']}.jpg")),
            "color": rec.get("color", ""),
            "width": rec.get("width") or 0,
            "height": rec.get("height") or 0,
            "tags": ", ".join(rec.get("tags", [])),
        })

    coll.add(ids=ids, documents=docs, metadatas=metas)
    print(f"Indexed {coll.count()} faces in 'faces' collection.")

    INDEXED_PATH.write_text(json.dumps(survivors, indent=2))
    print(f"Indexed manifest -> {INDEXED_PATH}")

    # confirm all collections present
    print("\nCollections in this database:")
    for c in client.list_collections():
        print(f"  - {c.name}: {c.count()} items")


if __name__ == "__main__":
    main()
