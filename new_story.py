#!/usr/bin/env python
"""
Stage a new story folder and seed without running any agents.

Usage:
    python new_story.py --seed "The seed text."
"""
import argparse, os, re, subprocess, sys
os.chdir(os.path.dirname(os.path.abspath(__file__)))
import config

parser = argparse.ArgumentParser()
parser.add_argument("--seed", required=True, help="Seed text for this narrative")
parser.add_argument("--run", action="store_true", help="Run the draft pipeline after staging.")
args = parser.parse_args()

SLUG_RE  = re.compile(r"^[a-z][a-z0-9_]{0,29}$")
ARTICLES = {"the", "a", "an"}


def _valid_slug(s: str) -> bool:
    if not SLUG_RE.match(s):
        return False
    if s.split("_")[0] in ARTICLES:
        return False
    return True


def _fallback_slug(seed: str) -> str:
    words = re.sub(r"[^a-zA-Z0-9 ]", "", seed).lower().split()
    filtered = [w for w in words if w not in ARTICLES][:3]
    return "_".join(filtered)[:30] or "story"


def _llm_slug(seed: str) -> str | None:
    prompt = (
        "Given this story seed, return one short slug — 1 to 3 words, lowercase, "
        "underscored if multiple words, no leading articles (the, a, an). The slug "
        "should capture the story's center: usually the protagonist's role, the "
        "central act, or the thematic core. Return only the slug. No explanation, "
        f"no quotes, no punctuation. Seed: {seed}"
    )
    try:
        import anthropic
        client = anthropic.Anthropic()
        for _ in range(2):
            resp = client.messages.create(
                model=config.SLUG_MODEL,
                max_tokens=20,
                messages=[{"role": "user", "content": prompt}],
            )
            candidate = resp.content[0].text.strip().lower().replace(" ", "_").replace("-", "_")
            if _valid_slug(candidate):
                return candidate
        return None
    except Exception:
        return None


slug = _llm_slug(args.seed.strip()) or _fallback_slug(args.seed.strip())

while True:
    answer = input(f"\nSuggested slug: {slug}\nUse this slug? [Y/n/edit]: ").strip().lower()
    if answer in ("", "y"):
        break
    elif answer == "n":
        print("Aborted.")
        sys.exit(0)
    elif answer == "edit":
        custom = input("Enter slug: ").strip()
        if not _valid_slug(custom):
            print("Invalid. Must be lowercase alphanumeric + underscores, no leading article, ≤30 chars.")
            continue
        slug = custom
        break
    else:
        print("Enter Y, n, or edit.")

import story_context
story_dir = story_context.set_story(slug)

seed_file   = story_dir / "seed.md"
existing    = seed_file.read_text() if seed_file.exists() else ""
has_content = existing.strip().replace("# Seed", "").strip()

if has_content:
    print(f"seed.md already has content:\n\n  {has_content[:120]}{'...' if len(has_content) > 120 else ''}\n")
    if input("Overwrite? [y/N] ").strip().lower() != "y":
        print("Aborted.")
        sys.exit(0)

seed_file.write_text(f"# Seed\n\n{args.seed.strip()}\n")

print(f"\nStory  : {slug}")
print(f"Folder : {story_dir}")
print(f"Seed   : {args.seed.strip()[:80]}{'...' if len(args.seed.strip()) > 80 else ''}")
print(f"\nNext:\n  python run_to_draft_01.py {slug}")

if args.run:
    print()
    subprocess.run([sys.executable, "run_to_draft_01.py", slug])
