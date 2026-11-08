#!/usr/bin/env python
"""
Editorial cut: draft_02 → draft_03.

Guha reads draft_02 cold, applies horst-prose, and produces a tightened
draft_03 plus a short editor's note.

Usage:
    python run_to_draft_03.py <narrative>
"""

import argparse
import os
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("narrative", help="Narrative slug, e.g. 'selective_forgetting'")
args = parser.parse_args()

import config
import story_context
story_context.set_story(args.narrative)

config.ensure_api_key()
import compatibility_patches  # must precede CrewAI imports — see compatibility_patches.py
import token_logger

drafts_dir = story_context.drafts_dir()
draft_path = drafts_dir / "draft_02.md" if drafts_dir else None

if not draft_path or not draft_path.exists():
    print(f"draft_02.md not found at {draft_path}")
    sys.exit(1)

draft_words = len(draft_path.read_text().split())
print(f"Narrative : {args.narrative}")
print(f"Draft     : {draft_path} ({draft_words} words)")

from crewai import Crew
from agents.guha import guha, build_task

print("\n" + "=" * 60)
print("GUHA — editorial cut")
print("=" * 60)

Crew(agents=[guha], tasks=[build_task()], verbose=False).kickoff()

draft3_path = drafts_dir / "draft_03.md" if drafts_dir else None

# Python-enforced word count: if over threshold, one retry pass
draft2_words = len(draft_path.read_text().split()) if draft_path and draft_path.exists() else 0
if draft3_path and draft3_path.exists() and draft2_words > 4500:
    draft3_words = len(draft3_path.read_text().split())
    target       = int(draft2_words * 0.85)
    if draft3_words > target:
        gap = draft3_words - target
        print(f"\ndraft_03 is {draft3_words} words — quota not met (target ≤{target}, gap {gap}). Running trim pass...")
        from agents.guha import build_trim_task
        Crew(agents=[guha], tasks=[build_trim_task(draft3_path, target)], verbose=False).kickoff()

if draft3_path and draft3_path.exists():
    words = len(draft3_path.read_text().split())
    print(f"\ndraft_03.md: {words} words at {draft3_path}")

    # Append metadata footer
    seed_path = story_context.story_dir() / "seed.md"
    seed_text = ""
    if seed_path.exists():
        for line in seed_path.read_text().splitlines():
            stripped = line.strip()
            if stripped and not stripped.startswith("#"):
                seed_text = stripped
                break

    footer = (
        f"\n\n---\n"
        f"System: unslop.  \n"
        f"Designed by: Rachel Horst (April 2026)  \n"
        f"Models: {config.MODEL.split('/')[-1]}  \n"
        f"Seed: {seed_text}\n"
    )
    with open(draft3_path, "a") as f:
        f.write(footer)
    print("Footer appended.")

else:
    print("\ndraft_03.md: not written")

letters_dir = story_context.letters_dir()
note_path = letters_dir / "guha_note.md" if letters_dir else None
if note_path and note_path.exists():
    words = len(note_path.read_text().split())
    print(f"guha_note.md: {words} words at {note_path}")
else:
    print("guha_note.md: not written")

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
