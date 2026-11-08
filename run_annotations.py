#!/usr/bin/env python
"""
Run annotation agents against draft_01 for a narrative.
Sue Pen (pass 1, pass 2) → Material → Miranda. Sequential.

Usage:
    python run_annotations.py <narrative>
"""

import argparse
import os
import sys

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("narrative", help="Narrative slug, e.g. 'dead_letters'")
args = parser.parse_args()

import story_context
story_context.set_story(args.narrative)

import token_logger

from crewai import Crew
from agents.sue_pen import sue_pen, build_pass1_task, build_pass2_task
from agents.material import material, build_pass1_task as material_pass1, build_pass2_task as material_pass2
from agents.miranda import miranda, build_annotation_task as miranda_task

drafts_dir = story_context.drafts_dir()
draft_path = drafts_dir / "draft_01.md" if drafts_dir else None

if not draft_path or not draft_path.exists():
    print(f"draft_01.md not found at {draft_path}")
    sys.exit(1)

print(f"Narrative : {args.narrative}")
print(f"Draft     : {draft_path}")

# ------------------------------------------------------------------ #
# Sue Pen — Pass 1                                                    #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SUE PEN — Pass 1")
print("=" * 60)

Crew(agents=[sue_pen], tasks=[build_pass1_task()], verbose=False).kickoff()

ann_dir = story_context.annotations_dir()
p1_path = ann_dir / "sue_pen.md" if ann_dir else None
if p1_path and p1_path.exists():
    print(f"\n{p1_path}:\n")
    print(p1_path.read_text())
else:
    print("\nsue_pen.md not written.")

# ------------------------------------------------------------------ #
# Sue Pen — Pass 2                                                    #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SUE PEN — Pass 2")
print("=" * 60)

Crew(agents=[sue_pen], tasks=[build_pass2_task()], verbose=False).kickoff()

if p1_path and p1_path.exists():
    print(f"\n{p1_path} (combined):\n")
    print(p1_path.read_text())
else:
    print("\nsue_pen.md not written.")

# ------------------------------------------------------------------ #
# Material                                                            #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MATERIAL — Pass 1")
print("=" * 60)

Crew(agents=[material], tasks=[material_pass1()], verbose=False).kickoff()

m_path = ann_dir / "material.md" if ann_dir else None
if m_path and m_path.exists():
    print(f"\n{m_path}:\n")
    print(m_path.read_text())
else:
    print("\nmaterial.md not written.")

print("\n" + "=" * 60)
print("MATERIAL — Pass 2")
print("=" * 60)

Crew(agents=[material], tasks=[material_pass2()], verbose=False).kickoff()

if m_path and m_path.exists():
    print(f"\n{m_path} (combined):\n")
    print(m_path.read_text())
else:
    print("\nmaterial.md not written.")

# ------------------------------------------------------------------ #
# Miranda                                                             #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MIRANDA — annotation")
print("=" * 60)

Crew(agents=[miranda], tasks=[miranda_task()], verbose=False).kickoff()

mir_path = ann_dir / "miranda.md" if ann_dir else None
if mir_path and mir_path.exists():
    print(f"\n{mir_path}:\n")
    print(mir_path.read_text())
else:
    print("\nmiranda.md not written.")

# ------------------------------------------------------------------ #
# Token report                                                        #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
