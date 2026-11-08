"""
pull_faces.py  (stage 1 of 2) — revised for visible expressions

Pulls portraits from Unsplash, biased toward faces with readable expressions.
Filters out arty/abstract results (silhouettes, hidden faces, hands-only).

Usage:
    export UNSPLASH_ACCESS_KEY="your_key"
    python pull_faces.py

Outputs:
    <repo>/faces/images/        — JPG files, named {unsplash_id}.jpg
    <repo>/faces/manifest.json  — full record of every face pulled

Notes:
    - Idempotent: existing files are skipped. Safe to re-run.
    - Pulls more candidates per query than we keep, then filters.
"""

import os
import json
import time
from pathlib import Path

import requests


UNSPLASH_KEY = os.environ.get("UNSPLASH_ACCESS_KEY")
if not UNSPLASH_KEY:
    raise SystemExit("Set UNSPLASH_ACCESS_KEY in your environment first.")

UNSLOP_ROOT = Path.home() / "unslop"
FACES_DIR = UNSLOP_ROOT / "faces"
IMAGES_DIR = FACES_DIR / "images"
MANIFEST_PATH = FACES_DIR / "manifest.json"

IMAGES_DIR.mkdir(parents=True, exist_ok=True)

# Generic, broad queries — let the filter do the work of weeding out
# artsy/abstract results. Each query pulls more candidates; we keep more
# per query to compensate for the smaller list.
QUERIES = [
    "face",
    "woman",
    "man",
    "child",
    "teenager",
    "elderly",
    "old woman",
    "old man",
    "smiling",
    "laughing",
    "serious face",
    "tired",
    "thinking",
    "worried",
    "person",
]

PER_QUERY_FETCH = 20    # fetch this many candidates
PER_QUERY_KEEP = 10     # keep up to this many after filtering

# Tag/description signals. Anything containing a NEGATIVE term gets
# rejected outright. POSITIVE terms boost score (used as ranking).
NEGATIVE_TERMS = {
    "silhouette", "shadow", "back of", "from behind", "rear view",
    "hands", "hand covering", "obscured", "blurred face", "out of focus",
    "abstract", "double exposure", "bokeh", "reflection",
    "mannequin", "statue", "sculpture", "doll", "mask",
    "covered face", "hidden face", "no face", "faceless",
    "anonymous", "unrecognizable",
}

POSITIVE_TERMS = {
    "face", "smile", "smiling", "laugh", "laughing", "eyes",
    "expression", "looking", "gaze", "portrait", "headshot",
    "close-up", "close up", "closeup",
}

SEARCH_URL = "https://api.unsplash.com/search/photos"
HEADERS = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}


def search(query: str, per_page: int) -> list[dict]:
    r = requests.get(
        SEARCH_URL,
        headers=HEADERS,
        params={"query": query, "per_page": per_page, "orientation": "portrait"},
        timeout=30,
    )
    r.raise_for_status()
    return r.json().get("results", [])


def trigger_download(photo: dict) -> None:
    url = photo.get("links", {}).get("download_location")
    if not url:
        return
    try:
        requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException:
        pass


def download_image(url: str, dest: Path) -> bool:
    if dest.exists():
        return True
    try:
        r = requests.get(url, timeout=60)
        r.raise_for_status()
        dest.write_bytes(r.content)
        return True
    except requests.RequestException as e:
        print(f"  ! download failed: {e}")
        return False


def text_blob(photo: dict) -> str:
    """Concatenate everything Unsplash gave us about the image, lowercased."""
    parts = [
        photo.get("description") or "",
        photo.get("alt_description") or "",
        " ".join(t.get("title", "") for t in photo.get("tags", []) if t.get("title")),
    ]
    return " ".join(parts).lower()


def score_photo(photo: dict):
    """Return a relevance score, or None if the photo should be rejected.
    Higher = more likely to show a clear face with expression."""
    blob = text_blob(photo)

    # hard rejects
    for neg in NEGATIVE_TERMS:
        if neg in blob:
            return None

    # if there's no description or tags at all, we can't tell — accept
    # cautiously with a low score
    if not blob.strip():
        return 0

    score = 0
    for pos in POSITIVE_TERMS:
        if pos in blob:
            score += 1
    return score


def shape_record(photo: dict, query: str, score: int) -> dict:
    user = photo.get("user", {}) or {}
    tags = [t.get("title", "") for t in photo.get("tags", []) if t.get("title")]
    return {
        "id": photo["id"],
        "query": query,
        "score": score,
        "description": photo.get("description") or "",
        "alt_description": photo.get("alt_description") or "",
        "tags": tags,
        "color": photo.get("color") or "",
        "width": photo.get("width"),
        "height": photo.get("height"),
        "image_url_regular": photo["urls"]["regular"],
        "unsplash_url": photo["links"]["html"],
        "photographer": user.get("name") or "",
        "photographer_username": user.get("username") or "",
        "photographer_url": (user.get("links") or {}).get("html") or "",
    }


def main() -> None:
    print(f"Pulling faces into {IMAGES_DIR}")
    print(f"Queries: {len(QUERIES)}  |  fetch {PER_QUERY_FETCH}/query, keep up to {PER_QUERY_KEEP}\n")

    existing = {}
    if MANIFEST_PATH.exists():
        for rec in json.loads(MANIFEST_PATH.read_text()):
            existing[rec["id"]] = rec
        print(f"Found existing manifest with {len(existing)} records — will merge.\n")

    seen_ids = set(existing.keys())
    records = list(existing.values())

    for i, query in enumerate(QUERIES, start=1):
        print(f"[{i:2d}/{len(QUERIES)}] {query!r}")
        try:
            results = search(query, PER_QUERY_FETCH)
        except requests.HTTPError as e:
            print(f"  ! search failed: {e}")
            continue

        # score and filter
        scored = []
        for photo in results:
            if photo["id"] in seen_ids:
                continue
            s = score_photo(photo)
            if s is None:
                continue
            scored.append((s, photo))

        # take top by score, up to PER_QUERY_KEEP
        scored.sort(key=lambda x: x[0], reverse=True)
        chosen = scored[:PER_QUERY_KEEP]

        kept = 0
        for s, photo in chosen:
            rec = shape_record(photo, query, s)
            dest = IMAGES_DIR / f"{rec['id']}.jpg"
            if not download_image(rec["image_url_regular"], dest):
                continue
            trigger_download(photo)
            rec["local_path"] = str(dest)
            records.append(rec)
            seen_ids.add(rec["id"])
            kept += 1

        rejected = len(results) - len(scored)
        print(f"     fetched {len(results)}, rejected {rejected}, kept {kept}, total {len(records)}")
        time.sleep(0.5)

    MANIFEST_PATH.write_text(json.dumps(records, indent=2))
    print(f"\nManifest -> {MANIFEST_PATH}")
    print(f"Images   -> {IMAGES_DIR} ({len(records)} faces)")
    print("\nNext: open the images folder, delete faces you don't want,")
    print("      then run: python index_faces.py")


if __name__ == "__main__":
    main()
