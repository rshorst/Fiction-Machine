#!/usr/bin/env python
"""
New-narrative run: Miranda → Frances → Richard (six plots).
Stops at six plots. Curator and draft writing are deferred.

Usage:
    python run_plots.py <narrative> --seed "The seed text."
    python run_plots.py <narrative>        # reads from vault/stories/<narrative>/seed.md
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

import story_context
story_dir = story_context.set_story(args.narrative)

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

from crewai import Crew
from agents.miranda import miranda, build_task as build_miranda_task
from agents.frances import frances, build_character_task
from agents.richard import richard, build_plots_task

# ------------------------------------------------------------------ #
# Phase 2 — Miranda: theory deposits                                  #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("MIRANDA — theory deposits")
print("=" * 60)

crew_miranda = Crew(agents=[miranda], tasks=[build_miranda_task(seed)], verbose=False)
crew_miranda.kickoff()

deposits_dir  = story_context.theory_deposits_dir()
deposit_files = sorted(deposits_dir.glob("*.md")) if deposits_dir and deposits_dir.exists() else []
print(f"\n{len(deposit_files)} deposit file(s) in {deposits_dir}")

# ------------------------------------------------------------------ #
# Phase 3 — Frances: characters                                       #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("FRANCES — characters")
print("=" * 60)

crew_frances = Crew(agents=[frances], tasks=[build_character_task()], verbose=False)
crew_frances.kickoff()

chars_dir  = story_context.characters_dir()
char_files = sorted(chars_dir.glob("*.md")) if chars_dir and chars_dir.exists() else []
print(f"\n{len(char_files)} character file(s) in {chars_dir}")

# ------------------------------------------------------------------ #
# Phase 4 — Richard: six plots                                        #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("RICHARD — six plots")
print("=" * 60)

crew_plots = Crew(agents=[richard], tasks=[build_plots_task(seed)], verbose=False)
crew_plots.kickoff()

p_dir      = story_context.plots_dir()
plots_path = p_dir / "plots.md" if p_dir else None
if plots_path and plots_path.exists():
    words = len(plots_path.read_text().split())
    print(f"\nplots.md: {words} words at {plots_path}")
else:
    print("\nplots.md: not found")

# ------------------------------------------------------------------ #
# Token report                                                        #
# ------------------------------------------------------------------ #

print("\n" + "=" * 60)
print("TOKEN COST")
print("=" * 60)
token_logger.report()
