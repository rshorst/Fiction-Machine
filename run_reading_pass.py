#!/usr/bin/env python
"""
Richard reading pass + Sue Pen pass on em_aberto.

Richard reads draft_01 as if someone else wrote it, annotates, writes draft_02.
Sue Pen reads draft_02, marks where it settled too early, writes sue_pen_draft.md.
"""

import os
os.chdir(os.path.dirname(os.path.abspath(__file__)))

import story_context
story_context.set_story("em_aberto")

import token_logger  # must be imported early to register litellm callbacks

from pathlib import Path
from crewai import Crew
from agents.richard import richard, build_reading_task
from agents.sue_pen import sue_pen, build_pass1_task, build_pass2_task

DRAFT_01   = "em_aberto_draft_01.md"
DRAFT_02   = "em_aberto_draft_02.md"
STORY_DIR  = Path("vault/stories/em_aberto")
DRAFTS_DIR = STORY_DIR / "drafts"

print("=" * 60)
print("RICHARD — reading pass on draft_01 → draft_02")
print("=" * 60)

task_richard = build_reading_task(
    draft_filename=DRAFT_01,
    draft_02_filename=DRAFT_02,
)
crew_richard = Crew(agents=[richard], tasks=[task_richard], verbose=False)
result_richard = crew_richard.kickoff()

print("\n--- RICHARD OUTPUT ---")
print(result_richard)

annotations = STORY_DIR / "annotations" / "richard_reading.md"
print(f"\nrichard_reading.md ({annotations.stat().st_size} bytes)" if annotations.exists() else "\nrichard_reading.md: not found")

draft_02 = DRAFTS_DIR / DRAFT_02
if draft_02.exists():
    words = len(draft_02.read_text().split())
    print(f"draft_02: {words} words at {draft_02}")
else:
    print(f"draft_02: not found at {draft_02}")

print("\n" + "=" * 60)
print("SUE PEN — exactness reading on draft_02")
print("=" * 60)

draft_source = draft_02 if draft_02.exists() else (DRAFTS_DIR / DRAFT_01)
raw_text     = draft_source.read_text() if draft_source.exists() else ""

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

numbered_text = _number_paragraphs(raw_text)
sue_draft     = STORY_DIR / "annotations" / "sue_pen_annotations.md"

print(f"\nSue Pen source: {draft_source.name} ({len(raw_text.split())} words)")

print("\nRunning Sue Pen Pass 1 — Associative ...")
task_sue_1    = build_pass1_task(numbered_text)
crew_sue_1    = Crew(agents=[sue_pen], tasks=[task_sue_1], verbose=False)
result_sue_1  = crew_sue_1.kickoff()
out1          = result_sue_1.raw if hasattr(result_sue_1, "raw") else str(result_sue_1)
sue_draft.write_text(
    f"# Sue Pen — {draft_source.name}\n\n## Pass 1 — Associative\n\n{out1.strip()}\n"
)
print(f"Pass 1 written to {sue_draft}")

print("\nRunning Sue Pen Pass 2 — Additive ...")
task_sue_2    = build_pass2_task(numbered_text)
crew_sue_2    = Crew(agents=[sue_pen], tasks=[task_sue_2], verbose=False)
result_sue_2  = crew_sue_2.kickoff()
out2          = result_sue_2.raw if hasattr(result_sue_2, "raw") else str(result_sue_2)
with open(sue_draft, "a") as f:
    f.write(f"\n\n## Pass 2 — Additive / Extractive\n\n{out2.strip()}\n")
print(f"Pass 2 appended to {sue_draft}")

if sue_draft.exists():
    words = len(sue_draft.read_text().split())
    print(f"\nsue_pen_annotations.md: {words} words at {sue_draft}")
else:
    print("\nsue_pen_annotations.md: not found")

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
