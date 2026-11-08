#!/usr/bin/env python
"""
Restore a story to its checkpoint state.

Deletes drafts/, annotations/, letters/, and plots/ then copies _checkpoint/
contents back. Use this when a run failed after Miranda+characters+relations
and you want to retry from that point without rerunning the upstream work.

Usage:
    python restore_checkpoint.py <narrative>
"""

import argparse
import os
import shutil
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

parser = argparse.ArgumentParser()
parser.add_argument("narrative", help="Narrative slug, e.g. 'my_narrative'")
args = parser.parse_args()

import story_context
story_dir = story_context.set_story(args.narrative)

cp_dir = story_dir / "_checkpoint"
if not cp_dir.exists():
    print(f"No checkpoint found at {cp_dir}")
    sys.exit(1)

for subdir in ("drafts", "annotations", "letters", "plots"):
    dst = story_dir / subdir
    if dst.exists():
        shutil.rmtree(dst)
        print(f"Removed {dst}")

for item in sorted(cp_dir.iterdir()):
    dst = story_dir / item.name
    if item.is_dir():
        shutil.copytree(item, dst)
    else:
        shutil.copy2(item, dst)
    print(f"Restored {item.name} → {dst}")

print(f"\nCheckpoint restored for '{args.narrative}'. Ready to re-run from plots/draft_01.")
