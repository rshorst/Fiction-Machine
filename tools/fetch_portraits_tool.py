"""
Select portrait photographs from the local face library at faces/images/.
Credit is pulled from faces/manifest.json where available.
No API calls. Frances never fails for lack of a face.
"""

import json
import random
import shutil
import sys
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import story_context

import config

FACES_DIR   = config.FACES_DIR
IMAGES_DIR  = FACES_DIR / "images"
MANIFEST    = FACES_DIR / "manifest.json"

_manifest_index: dict | None = None


def _load_manifest() -> dict:
    global _manifest_index
    if _manifest_index is None:
        if MANIFEST.exists():
            entries = json.loads(MANIFEST.read_text())
            _manifest_index = {e["id"]: e for e in entries}
        else:
            _manifest_index = {}
    return _manifest_index


def _credit(img_id: str) -> str:
    entry = _load_manifest().get(img_id)
    if entry:
        photographer = entry.get("photographer", "unknown")
        url = entry.get("unsplash_url", "")
        return f"Photo by {photographer} on Unsplash ({url})"
    return f"Local library: {img_id}.jpg"


class FetchPortraitsInput(BaseModel):
    count: int = Field(default=1, description="Number of portraits to select (default 1)")
    query: str = Field(default="", description="Ignored — portraits are drawn from the local library.")


class FetchPortraitsTool(BaseTool):
    name: str = "Fetch Portraits"
    description: str = (
        "Select portrait photographs from the local face library for character building. "
        "Returns the file path and photographer credit for each portrait. "
        "Portraits are pre-curated contemporary faces in everyday register."
    )
    args_schema: Type[BaseModel] = FetchPortraitsInput

    def _run(self, count: int = 1, query: str = "") -> str:
        candidates = sorted(IMAGES_DIR.glob("*.jpg"))
        if not candidates:
            return f"No portraits found in {IMAGES_DIR}."

        story_faces = story_context.faces_dir()
        used_path = (story_faces / "used.json") if story_faces else None
        used_ids: set[str] = set()
        if used_path and used_path.exists():
            try:
                used_ids = set(json.loads(used_path.read_text()))
            except (json.JSONDecodeError, OSError):
                used_ids = set()

        available = [c for c in candidates if c.stem not in used_ids] or candidates
        chosen = random.sample(available, min(count, len(available)))

        if story_faces:
            story_faces.mkdir(parents=True, exist_ok=True)
            for path in chosen:
                dst = story_faces / path.name
                if not dst.exists():
                    shutil.copy2(path, dst)
            if used_path is not None:
                try:
                    used_path.write_text(json.dumps(list(used_ids | {p.stem for p in chosen})))
                except OSError as e:
                    print(f"[FetchPortraitsTool] warning: could not update used.json: {e}", file=sys.stderr)

        lines = [f"Selected {len(chosen)} portrait(s):\n"]
        for i, path in enumerate(chosen, 1):
            lines.append(f"Portrait {i}:")
            lines.append(f"  File: {path}")
            lines.append(f"  Credit: {_credit(path.stem)}")
            lines.append("")
        return "\n".join(lines)
