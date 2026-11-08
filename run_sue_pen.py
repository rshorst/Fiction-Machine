#!/usr/bin/env python
"""
Run Sue Pen on a draft in two passes.

Pass 1 — Associative: paragraph-keyed marks, sideways thinking, replacements and questions.
Pass 2 — Additive/Extractive: returns to key passages, gives the world what was left out.

Both passes written to vault/stories/[story]/annotations/sue_pen_annotations.md.

Usage:
  venv-crewai/bin/python run_sue_pen.py                                    # draft_02
  venv-crewai/bin/python run_sue_pen.py em_aberto_draft_01.md              # named draft
  venv-crewai/bin/python run_sue_pen.py em_aberto_draft_02.md out.md       # custom output name
"""

import os
import sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import story_context
story_context.set_story("em_aberto")

import token_logger  # must be early

from pathlib import Path
from crewai import Crew
from agents.sue_pen import sue_pen, build_pass1_task, build_pass2_task

DRAFT  = sys.argv[1] if len(sys.argv) > 1 else "em_aberto_draft_02.md"
OUTFILE = sys.argv[2] if len(sys.argv) > 2 else "sue_pen_annotations.md"
draft_path = story_context.drafts_dir() / DRAFT

if not draft_path.exists():
    print(f"Draft not found: {draft_path}")
    sys.exit(1)

output_path = story_context.annotations_dir() / OUTFILE


def _number_paragraphs(text: str) -> str:
    """Prefix each non-empty paragraph with [¶N] so Sue Pen can key marks to it."""
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


def _run_pass(task) -> str:
    crew = Crew(agents=[sue_pen], tasks=[task], verbose=False)
    result = crew.kickoff()
    raw = result.raw if hasattr(result, "raw") else str(result)
    return raw.strip()


# ------------------------------------------------------------------ #
# Prepare draft text with paragraph numbers                          #
# ------------------------------------------------------------------ #

raw_text = draft_path.read_text()
numbered_text = _number_paragraphs(raw_text)
paragraph_count = sum(1 for p in raw_text.split("\n\n") if p.strip())

print(f"Draft: {DRAFT} ({paragraph_count} paragraphs)")
print("=" * 60)

# ------------------------------------------------------------------ #
# Pass 1 — Associative                                               #
# ------------------------------------------------------------------ #

print("\nRunning Pass 1 — Associative ...")
task1 = build_pass1_task(numbered_text)
out1 = _run_pass(task1)

output_path.write_text(
    f"# Sue Pen — {DRAFT}\n\n"
    f"## Pass 1 — Associative\n\n"
    f"{out1}\n"
)
print(f"Pass 1 written to {output_path}")

# ------------------------------------------------------------------ #
# Pass 2 — Additive / Extractive                                     #
# ------------------------------------------------------------------ #

print("\nRunning Pass 2 — Additive / Extractive ...")
task2 = build_pass2_task(numbered_text)
out2 = _run_pass(task2)

with open(output_path, "a") as f:
    f.write(f"\n\n## Pass 2 — Additive / Extractive\n\n{out2}\n")
print(f"Pass 2 appended to {output_path}")

# ------------------------------------------------------------------ #
# Print combined output                                              #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("SUE PEN — COMBINED OUTPUT")
print("=" * 60 + "\n")
print(output_path.read_text())

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
