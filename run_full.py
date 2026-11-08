#!/usr/bin/env python
"""
Full pipeline: seed → draft_03.pdf

Usage:
    python run_full.py --seed "Your seed text here."
    python run_full.py --seed "..." --slug my_story --yes   # no questions asked
"""

import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Prevent macOS sleep during long run
if sys.platform == "darwin" and "CAFFEINATE_ACTIVE" not in os.environ:
    if shutil.which("caffeinate"):
        env = {**os.environ, "CAFFEINATE_ACTIVE": "1"}
        os.execvpe("caffeinate", ["caffeinate", "-i", sys.executable] + sys.argv, env)

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import argparse
parser = argparse.ArgumentParser()
parser.add_argument("--seed", required=True, help="Seed text for this narrative")
parser.add_argument("--slug", help="Folder name for this story (lowercase_with_underscores). Skips the suggestion step.")
parser.add_argument("--yes", "-y", action="store_true", help="Accept the suggested slug without asking.")
args = parser.parse_args()
seed = args.seed.strip()

import config
config.ensure_api_key()

BASE   = Path(__file__).parent
PYTHON = sys.executable

# ── Slug derivation ──────────────────────────────────────────────────
ARTICLES = {"the", "a", "an"}
SLUG_RE  = re.compile(r"^[a-z][a-z0-9_]{0,29}$")


def _valid_slug(s: str) -> bool:
    return bool(SLUG_RE.match(s)) and s.split("_")[0] not in ARTICLES


def _fallback_slug(text: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", "", text).lower().split()
    return "_".join(w for w in words if w not in ARTICLES)[:30] or "story"


def _llm_slug(text: str) -> str | None:
    try:
        import anthropic
        client = anthropic.Anthropic()
        prompt = (
            "Given this story seed, return one short slug — 1 to 3 words, lowercase, "
            "underscored, no leading articles. Capture the story's center: protagonist's "
            "role, central act, or thematic core. Return only the slug. "
            f"Seed: {text}"
        )
        for _ in range(2):
            resp = client.messages.create(
                model=config.SLUG_MODEL, max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            candidate = resp.content[0].text.strip().lower().replace(" ", "_").replace("-", "_")
            if _valid_slug(candidate):
                return candidate
    except Exception:
        pass
    return None


if args.slug:
    if not _valid_slug(args.slug):
        sys.exit("Invalid --slug: lowercase letters, digits and underscores, no leading article, 30 characters max.")
    slug = args.slug
else:
    slug = _llm_slug(seed) or _fallback_slug(seed)

while not (args.slug or args.yes):
    answer = input(f"\nSuggested slug: {slug}\nUse this slug? [Y/n/edit]: ").strip().lower()
    if answer in ("", "y"):
        break
    if answer == "n":
        print("Aborted.")
        sys.exit(0)
    if answer == "edit":
        custom = input("Enter slug: ").strip()
        if _valid_slug(custom):
            slug = custom
            break
        print("Invalid — lowercase + underscores, no leading article, ≤30 chars.")

# ── Stage story ──────────────────────────────────────────────────────
import story_context
story_dir = story_context.set_story(slug)
seed_file = story_dir / "seed.md"
seed_file.write_text(f"# Seed\n\n{seed}\n")

print(f"\nStory : {slug}")
print(f"Seed  : {seed[:80]}{'...' if len(seed) > 80 else ''}")
print(f"Dir   : {story_dir}")

# ── Run pipeline ─────────────────────────────────────────────────────
STAGES = [
    ("run_to_draft_01.py", "Draft 01  (Miranda → Frances → Richard)"),
    ("run_to_draft_02.py", "Draft 02  (Sue Pen → Material → Miranda → Sean → Richard)"),
    ("run_to_draft_03.py", "Draft 03  (Guha editorial cut)"),
]

completed = []
for script, label in STAGES:
    print(f"\n{'=' * 60}\nSTAGE: {label}\n{'=' * 60}")
    r = subprocess.run([PYTHON, str(BASE / script), slug], cwd=str(BASE))
    if r.returncode != 0:
        print(f"\n{script} failed (exit {r.returncode}). Stopping.")
        sys.exit(r.returncode)
    completed.append(label)

# ── Generate PDF ─────────────────────────────────────────────────────
draft3 = story_dir / "drafts" / "draft_03.md"
pdf    = story_dir / "drafts" / f"{slug}.pdf"
if draft3.exists():
    from generate_pdf import make_pdf
    make_pdf(draft3, pdf)
else:
    print("\nWarning: draft_03.md not found — skipping PDF.")

# ── Corpus inventory ─────────────────────────────────────────────────
import update_corpus_inventory
update_corpus_inventory.main()

# ── Summary ──────────────────────────────────────────────────────────
print(f"\n{'=' * 60}\nPIPELINE COMPLETE\n{'=' * 60}")
print(f"Stages : {', '.join(completed)}")
if draft3.exists():
    print(f"Draft  : {draft3} ({len(draft3.read_text().split())} words)")
if pdf.exists():
    print(f"PDF    : {pdf}")

LOG = config.OUTPUTS / "token_log.jsonl"
if LOG.exists():
    records    = [json.loads(l) for l in LOG.read_text().splitlines() if l.strip()]
    run_cost   = sum(r["cost"] for r in records if r.get("slug") == slug)
    run_calls  = sum(1 for r in records if r.get("slug") == slug)
    total_cost = sum(r["cost"] for r in records)
    print(f"Cost   : ${run_cost:.4f} this run ({run_calls} calls) | ${total_cost:.4f} all-time")
