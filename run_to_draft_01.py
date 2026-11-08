#!/usr/bin/env python
"""
Full narrative run through draft 01:
Miranda → Frances → Richard (six plots) → Curator (selection) → Richard (draft 01).

Usage:
    python run_to_draft_01.py <narrative> --seed "The seed text."
    python run_to_draft_01.py <narrative>        # reads from vault/stories/<narrative>/seed.md
"""

import argparse
import os
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("narrative", help="Narrative slug, e.g. 'my_narrative'")
parser.add_argument("--seed", help="Seed text (overrides seed.md if present)")
args = parser.parse_args()

import config
import story_context
story_dir = story_context.set_story(args.narrative)

config.ensure_api_key()
import compatibility_patches  # must precede CrewAI imports — see compatibility_patches.py
import token_logger  # must be imported early to register litellm callbacks

SEED_FILE = story_dir / "seed.md"

if args.seed:
    seed = args.seed.strip()
    SEED_FILE.write_text(f"# Seed\n\n{seed}\n")
elif SEED_FILE.exists():
    raw   = SEED_FILE.read_text()
    lines = [l for l in raw.splitlines() if not l.startswith("# Seed")]
    seed  = "\n".join(lines).strip()
    if not seed:
        print(f"Error: {SEED_FILE} is empty. Pass --seed 'text' or write a seed into it.")
        sys.exit(1)
else:
    print(f"Error: no seed found. Pass --seed 'text' or create {SEED_FILE}.")
    sys.exit(1)

print(f"Narrative : {args.narrative}")
print(f"Seed      : {seed[:80]}{'...' if len(seed) > 80 else ''}")
print(f"Story dir : {story_dir}")

# Resume state — computed once before any kickoffs
_deps_dir      = story_context.theory_deposits_dir()
_existing_deps = len(list(_deps_dir.glob("*.md"))) if _deps_dir and _deps_dir.exists() else 0
_chars_dir0    = story_context.characters_dir()
_existing_chars = len(list(_chars_dir0.glob("*.md"))) if _chars_dir0 and _chars_dir0.exists() else 0
if _existing_deps or _existing_chars:
    print(f"Resume    : {_existing_deps} deposit(s), {_existing_chars} character(s) already done")

from crewai import Crew
from agents.miranda import miranda, build_task as build_miranda_task
from agents.frances import frances, build_character_task, build_relations_task
from agents.richard import richard, build_plots_task, build_draft_task
from agents.curator import curator, build_plot_selection_task

# ------------------------------------------------------------------ #
# Miranda: theory deposits                                            #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MIRANDA — theory deposits")
print("=" * 60)

if _existing_deps >= 3:
    print(f"Skipping — {_existing_deps} deposits already exist.")
else:
    crew_miranda = Crew(agents=[miranda], tasks=[build_miranda_task(seed)], verbose=False)
    crew_miranda.kickoff()

deposits_dir  = story_context.theory_deposits_dir()
deposit_files = sorted(deposits_dir.glob("*.md")) if deposits_dir and deposits_dir.exists() else []
print(f"\n{len(deposit_files)} deposit file(s) in {deposits_dir}")

# ------------------------------------------------------------------ #
# Frances: characters                                                 #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("FRANCES — characters")
print("=" * 60)

for _char_n in range(1, 4):
    if _char_n <= _existing_chars:
        print(f"  character {_char_n}/3: already done, skipping")
        continue
    print(f"  character {_char_n}/3")
    Crew(agents=[frances], tasks=[build_character_task()], verbose=False).kickoff()

chars_dir  = story_context.characters_dir()
char_files = sorted(chars_dir.glob("*.md")) if chars_dir and chars_dir.exists() else []
print(f"\n{len(char_files)} character file(s) in {chars_dir}")

# ------------------------------------------------------------------ #
# Frances: relational web                                             #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("FRANCES — relational web")
print("=" * 60)

_rels_path = (story_context.characters_dir() / "relations.md") if story_context.characters_dir() else None
if _rels_path and _rels_path.exists():
    print("Skipping — relations.md already exists.")
else:
    Crew(agents=[frances], tasks=[build_relations_task()], verbose=False).kickoff()

if _rels_path and _rels_path.exists():
    words = len(_rels_path.read_text().split())
    print(f"\nrelations.md: {words} words at {_rels_path}")
else:
    print("\nrelations.md: not written")

# ------------------------------------------------------------------ #
# Checkpoint                                                          #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("CHECKPOINT")
print("=" * 60)

import shutil as _shutil
_story_dir = story_context.story_dir()
_cp_dir    = _story_dir / "_checkpoint" if _story_dir else None
if _cp_dir:
    _cp_dir.mkdir(parents=True, exist_ok=True)
    _seed = _story_dir / "seed.md"
    if _seed.exists():
        _shutil.copy2(_seed, _cp_dir / "seed.md")
    for _subdir in ("theory_deposits", "characters", "faces"):
        _src = _story_dir / _subdir
        if _src.exists():
            _dst = _cp_dir / _subdir
            if _dst.exists():
                _shutil.rmtree(_dst)
            _shutil.copytree(_src, _dst)
    print(f"Checkpoint saved to {_cp_dir}")
else:
    print("Checkpoint skipped — no story dir.")

# ------------------------------------------------------------------ #
# Richard: six plots                                                  #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("RICHARD — six plots")
print("=" * 60)

p_dir      = story_context.plots_dir()
plots_path = p_dir / "plots.md" if p_dir else None
if plots_path and plots_path.exists():
    print("Skipping — plots.md already exists.")
else:
    crew_plots = Crew(agents=[richard], tasks=[build_plots_task(seed)], verbose=False)
    crew_plots.kickoff()

if plots_path and plots_path.exists():
    words = len(plots_path.read_text().split())
    print(f"\nplots.md: {words} words at {plots_path}")
else:
    print("\nplots.md: not found")

# ------------------------------------------------------------------ #
# Curator: plot selection                                             #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("CURATOR — plot selection")
print("=" * 60)

sel_path = p_dir / "curator_selection.md" if p_dir else None
if sel_path and sel_path.exists():
    print("Skipping — curator_selection.md already exists.")
else:
    crew_curator = Crew(agents=[curator], tasks=[build_plot_selection_task()], verbose=False)
    crew_curator.kickoff()

if sel_path and sel_path.exists():
    words = len(sel_path.read_text().split())
    print(f"\ncurator_selection.md: {words} words at {sel_path}")
else:
    print("\ncurator_selection.md: not found")

# ------------------------------------------------------------------ #
# Richard: draft 01                                                   #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("RICHARD — draft 01")
print("=" * 60)

drafts_dir = story_context.drafts_dir()
draft_path = drafts_dir / "draft_01.md" if drafts_dir else None
if draft_path and draft_path.exists():
    print("Skipping — draft_01.md already exists.")
else:
    crew_draft = Crew(agents=[richard], tasks=[build_draft_task()], verbose=False)
    crew_draft.kickoff()

if draft_path and draft_path.exists():
    words = len(draft_path.read_text().split())
    print(f"\ndraft_01.md: {words} words at {draft_path}")
else:
    print("\ndraft_01.md: not found")

# ------------------------------------------------------------------ #
# Token report                                                        #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
