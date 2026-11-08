"""
pull_faces_round2.py — additive second pass

Adds faces in the 30s–60s age range and broader cultural range.
Reads the existing manifest and image folder, skips anything already there.
Only adds new faces.

Usage:
    export UNSPLASH_ACCESS_KEY="your_key"
    python pull_faces_round2.py

Outputs:
    Appends to <repo>/faces/images/ and <repo>/faces/manifest.json
    Existing files and entries are untouched.
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

# Round 2: middle-aged adults, broader cultural range.
# Place-name terms tend to pull documentary work by photographers from
# those places — better than racial-category terms, which return more stock.
QUERIES = [
    # age signals
    "middle aged woman",
    "middle aged man",
    "adult face",
    "mature woman face",
    "mature man face",
    # cultural / geographic range
    "nigerian woman",
    "nigerian man",
    "kenyan woman",
    "ethiopian man",
    "ghanaian face",
    "south african face",
    "moroccan woman",
    "egyptian man",
    "indian woman face",
    "indian man face",
    "pakistani face",
    "bangladeshi face",
    "vietnamese woman",
    "thai man",
    "indonesian face",
    "filipino face",
    "japanese face",
    "korean face",
    "chinese face",
    "mexican woman",
    "brazilian face",
    "peruvian face",
    "colombian face",
    "iranian face",
    "turkish face",
]

PER_QUERY_FETCH = 15
PER_QUERY_KEEP = 5

NEGATIVE_TERMS = {
    "silhouette", "shadow", "back of", "from behind", "rear view",
    "hands", "hand covering", "obscured", "blurred face", "out of focus",
    "abstract", "double exposure", "bokeh", "reflection",
    "mannequin", "statue", "sculpture", "doll", "mask",
    "covered face", "hidden face", "no face", "faceless",
    "anonymous", "unrecognizable",
    # round-2 additions: filter out obvious child/teen results that slip
    # through age-targeted queries
    "child", "kid", "baby", "toddler", "infant", "schoolboy", "schoolgirl",
}

POSITIVE_TERMS = {
    "face", "smile", "smiling", "laugh", "laughing", "eyes",
    "expression", "looking", "gaze", "portrait", "headshot",
    "close-up", "close up", "closeup",
    # round-2 additions
    "adult", "middle-aged", "mature", "professional",
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
    parts = [
        photo.get("description") or "",
        photo.get("alt_description") or "",
        " ".join(t.get("title", "") for t in photo.get("tags", []) if t.get("title")),
    ]
    return " ".join(parts).lower()


def score_photo(photo: dict):
    blob = text_blob(photo)
    for neg in NEGATIVE_TERMS:
        if neg in blob:
            return None
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
    print(f"Round 2: middle-aged + multicultural")
    print(f"Pulling into {IMAGES_DIR}")
    print(f"Queries: {len(QUERIES)}  |  fetch {PER_QUERY_FETCH}/query, keep up to {PER_QUERY_KEEP}\n")

    existing = {}
    if MANIFEST_PATH.exists():
        for rec in json.loads(MANIFEST_PATH.read_text()):
            existing[rec["id"]] = rec
        print(f"Existing manifest: {len(existing)} faces — these will be preserved.\n")

    seen_ids = set(existing.keys())
    records = list(existing.values())
    starting_count = len(records)

    for i, query in enumerate(QUERIES, start=1):
        print(f"[{i:2d}/{len(QUERIES)}] {query!r}")
        try:
            results = search(query, PER_QUERY_FETCH)
        except requests.HTTPError as e:
            print(f"  ! search failed: {e}")
            continue

        scored = []
        for photo in results:
            if photo["id"] in seen_ids:
                continue
            s = score_photo(photo)
            if s is None:
                continue
            scored.append((s, photo))

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
    added = len(records) - starting_count
    print(f"\nManifest -> {MANIFEST_PATH}")
    print(f"Started with {starting_count}, added {added}, total {len(records)} faces.")


if __name__ == "__main__":
    main()
