#!/usr/bin/env python
"""
Annotation pipeline + revision: draft_01 → draft_02.

Sue Pen (pass 1, pass 2) → Material (pass 1, pass 2) → Miranda →
Sean (editorial letter) → Richard (draft_02).

Usage:
    python run_to_draft_02.py <narrative>
"""

import argparse
import os
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("narrative", help="Narrative slug, e.g. 'dead_letters'")
args = parser.parse_args()

import config
import story_context
story_context.set_story(args.narrative)

config.ensure_api_key()
import compatibility_patches  # must precede CrewAI imports — see compatibility_patches.py
import token_logger  # must be imported early to register litellm callbacks

drafts_dir = story_context.drafts_dir()
draft_path = drafts_dir / "draft_01.md" if drafts_dir else None

if not draft_path or not draft_path.exists():
    print(f"draft_01.md not found at {draft_path}")
    sys.exit(1)

draft_words = len(draft_path.read_text().split())
print(f"Narrative : {args.narrative}")
print(f"Draft     : {draft_path} ({draft_words} words)")

from crewai import Crew
from agents.sue_pen import sue_pen, build_pass1_task as sp_pass1, build_pass2_task as sp_pass2
from agents.material import material, build_pass1_task as mat_pass1, build_pass2_task as mat_pass2
from agents.frances import frances, build_annotation_task as frances_annotation
from agents.miranda import miranda, build_annotation_task as miranda_task
from agents.sean import sean, build_task as sean_task
from agents.richard import richard, build_revision_task


def _ann_report(label: str, filename: str) -> None:
    ann_dir = story_context.annotations_dir()
    p = ann_dir / filename if ann_dir else None
    if p and p.exists():
        words = len(p.read_text().split())
        print(f"\n{filename}: {words} words at {p}")
    else:
        print(f"\n{filename}: not written")


# ------------------------------------------------------------------ #
# Sue Pen — Pass 1                                                    #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SUE PEN — Pass 1")
print("=" * 60)

Crew(agents=[sue_pen], tasks=[sp_pass1()], verbose=False).kickoff()
_ann_report("Sue Pen P1", "sue_pen.md")

# ------------------------------------------------------------------ #
# Sue Pen — Pass 2                                                    #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SUE PEN — Pass 2")
print("=" * 60)

Crew(agents=[sue_pen], tasks=[sp_pass2()], verbose=False).kickoff()
_ann_report("Sue Pen P2", "sue_pen.md")

# ------------------------------------------------------------------ #
# Material — Pass 1                                                   #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MATERIAL — Pass 1")
print("=" * 60)

Crew(agents=[material], tasks=[mat_pass1()], verbose=False).kickoff()
_ann_report("Material P1", "material.md")

# ------------------------------------------------------------------ #
# Material — Pass 2                                                   #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MATERIAL — Pass 2")
print("=" * 60)

Crew(agents=[material], tasks=[mat_pass2()], verbose=False).kickoff()
_ann_report("Material P2", "material.md")

# ------------------------------------------------------------------ #
# Frances — character annotation                                      #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("FRANCES — character annotation")
print("=" * 60)

Crew(agents=[frances], tasks=[frances_annotation()], verbose=False).kickoff()
_ann_report("Frances", "frances.md")

# ------------------------------------------------------------------ #
# Miranda — annotation                                                #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MIRANDA — annotation")
print("=" * 60)

Crew(agents=[miranda], tasks=[miranda_task()], verbose=False).kickoff()
_ann_report("Miranda", "miranda.md")

# ------------------------------------------------------------------ #
# Sean — editorial letter                                             #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SEAN — editorial letter")
print("=" * 60)

Crew(agents=[sean], tasks=[sean_task()], verbose=False).kickoff()

letters_dir = story_context.letters_dir()
letter_path = letters_dir / "sean_letter.md" if letters_dir else None
if letter_path and letter_path.exists():
    words = len(letter_path.read_text().split())
    print(f"\nsean_letter.md: {words} words at {letter_path}")
else:
    print("\nsean_letter.md: not written")

# ------------------------------------------------------------------ #
# Richard — draft 02                                                  #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("RICHARD — draft 02")
print("=" * 60)

Crew(agents=[richard], tasks=[build_revision_task()], verbose=False).kickoff()

draft2_path = drafts_dir / "draft_02.md" if drafts_dir else None
if draft2_path and draft2_path.exists():
    words = len(draft2_path.read_text().split())
    print(f"\ndraft_02.md: {words} words at {draft2_path}")
else:
    print("\ndraft_02.md: not written")

# ------------------------------------------------------------------ #
# Token report                                                        #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
