#!/usr/bin/env python
"""
Run Sean on a draft + accumulated annotations.

Sean delivers two verdicts: sentence level (smooth vs. earned) and arc level
(which arc, current position, what arrest requires).

Output: vault/stories/[story]/annotations/sean_annotations.md

Usage:
  venv-crewai/bin/python run_sean.py                          # draft_02 + all annotations
  venv-crewai/bin/python run_sean.py em_aberto_draft_02.md    # named draft
"""

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import story_context
story_context.set_story("em_aberto")

import token_logger  # must be early

from pathlib import Path
from crewai import Crew
from agents.sean import sean, build_task

DRAFT   = sys.argv[1] if len(sys.argv) > 1 else "em_aberto_draft_02.md"
draft_path  = story_context.drafts_dir() / DRAFT
ann_dir     = story_context.annotations_dir()
output_path = ann_dir / "sean_annotations.md"

if not draft_path.exists():
    print(f"Draft not found: {draft_path}")
    sys.exit(1)


def _number_paragraphs(text: str) -> str:
    paragraphs = text.split("\n\n")
    numbered = []
    n = 0
    for p in paragraphs:
        if p.strip():
            n += 1
            numbered.append(f"[¶{n}]\n{p}")
        else:
            numbered.append(p)
    return "\n\n".join(numbered)


def _load_annotations() -> str:
    """Load all annotation files except any previous sean_annotations."""
    if not ann_dir or not ann_dir.exists():
        return "(no annotations found)"
    files = sorted(ann_dir.glob("*.md"))
    # Load the canonical sue_pen and richard files; skip old versioned sue_pen runs
    priority = ["richard_reading.md", "sue_pen_annotations.md"]
    loaded = []
    for name in priority:
        p = ann_dir / name
        if p.exists():
            loaded.append(f"### {name}\n\n{p.read_text().strip()}")
    # Any others that aren't sue_pen versioned files or sean's own output
    skip = set(priority + ["sean_annotations.md"])
    for f in files:
        # skip versioned/test sue_pen files — only canonical sue_pen_annotations.md counts
        if f.name not in skip and not f.name.startswith("sue_pen_annotations"):
            loaded.append(f"### {f.name}\n\n{f.read_text().strip()}")
    if not loaded:
        return "(no annotations found)"
    return "\n\n---\n\n".join(loaded)


raw_draft    = draft_path.read_text()
numbered     = _number_paragraphs(raw_draft)
annotations  = _load_annotations()
para_count   = sum(1 for p in raw_draft.split("\n\n") if p.strip())

print(f"Draft: {DRAFT} ({para_count} paragraphs)")
print(f"Annotations loaded: {len(annotations.split())} words")
print("=" * 60)
print("Running Sean ...")

task = build_task(numbered, annotations)
crew = Crew(agents=[sean], tasks=[task], verbose=False)
result = crew.kickoff()
raw = result.raw if hasattr(result, "raw") else str(result)

output_path.write_text(
    f"# Sean — {DRAFT}\n\n{raw.strip()}\n"
)

print(f"Written to {output_path}")
print("\n" + "=" * 60)
print("SEAN — OUTPUT")
print("=" * 60 + "\n")
print(output_path.read_text())

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
