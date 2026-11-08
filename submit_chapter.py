#!/usr/bin/env python
"""
Send a finished story to the Fiction Machine book.

Turns vault/stories/<slug>/drafts/draft_03.md into a chapter under your name
(book/chapters/<title>.md), checks it, and sends it in as a pull request.
Rachel Horst reads every chapter before adding it to the book. Only the final
story and its note are sent; your drafts, annotations and letters stay here.
Chapters are shared under CC BY-NC 4.0.

Usage:
    python submit_chapter.py <slug>
    python submit_chapter.py <slug> --name "Your Name"
    python submit_chapter.py <slug> --no-send     # make the chapter file only
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

os.chdir(os.path.dirname(os.path.abspath(__file__)))

import book_tools as bt
import config

UPSTREAM = "rshorst/Fiction-Machine"
LICENCE = "I agree to share this chapter under the Creative Commons Attribution-NonCommercial 4.0 licence (CC BY-NC 4.0)."


def run(*cmd, check=True):
    return subprocess.run(cmd, check=check, capture_output=True, text=True)


def ask(question: str, default: str = "") -> str:
    if not sys.stdin.isatty():
        return default
    answer = input(question).strip()
    return answer or default


def web_instructions(path: Path) -> None:
    print(f"""
To send it from the GitHub website instead:
  1. Sign in to GitHub and open https://github.com/{UPSTREAM}/tree/main/book/chapters
  2. Click "Add file", then "Upload files", and drop in:
     {path.resolve()}
  3. Under the files, choose "Create a new branch" and click "Propose changes",
     then "Create pull request". In the description, include:
     "{LICENCE}"
Rachel gets an email and reads it before it goes into the book.""")


def send_with_gh(path: Path, title: str) -> bool:
    """Fork, branch, commit, push and open a pull request with the GitHub CLI."""
    if not shutil.which("gh") or not shutil.which("git"):
        return False
    if run("gh", "auth", "status", check=False).returncode != 0:
        print("\nThe GitHub CLI (gh) is installed but not signed in. Run: gh auth login")
        return False
    try:
        login = run("gh", "api", "user", "-q", ".login").stdout.strip()
        branch = f"chapter-{path.stem}"
        run("gh", "repo", "fork", UPSTREAM, "--clone=false")
        remotes = run("git", "remote").stdout.split()
        if "fork" not in remotes:
            run("git", "remote", "add", "fork", f"https://github.com/{login}/{UPSTREAM.split('/')[1]}.git")
        start = run("git", "rev-parse", "--abbrev-ref", "HEAD").stdout.strip()
        run("git", "fetch", "https://github.com/" + UPSTREAM + ".git", "main")
        run("git", "checkout", "-b", branch, "FETCH_HEAD")
        run("git", "add", str(path))
        run("git", "commit", "-m", f"Add chapter: {title}")
        run("git", "push", "-u", "fork", branch)
        pr = run("gh", "pr", "create", "--repo", UPSTREAM, "--head", f"{login}:{branch}",
                 "--title", f"Chapter: {title}",
                 "--body", f"A new chapter for the book, made with the Fiction Machine.\n\n- [x] {LICENCE}")
        run("git", "checkout", start, check=False)
        print(f"\nSent. Your pull request: {pr.stdout.strip()}")
        print("Rachel gets an email and reads it before it goes into the book.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\nCouldn't send it automatically:\n{(e.stderr or e.stdout or '').strip()}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Send a finished story to the Fiction Machine book.")
    parser.add_argument("slug", help="The story's folder name in vault/stories/")
    parser.add_argument("--name", help="Your name as it should appear in the book")
    parser.add_argument("--no-send", action="store_true", help="Only make the chapter file")
    args = parser.parse_args()

    draft = config.VAULT / "stories" / args.slug / "drafts" / "draft_03.md"
    if not draft.exists():
        sys.exit(f"No finished story at {draft}. Run the machine to the end first.")

    name = args.name or ask("Your name, as it should appear in the book: ")
    if not name:
        sys.exit("A name is needed. Use --name \"Your Name\".")

    filename, text = bt.from_draft(draft, run_by=name)
    bt.CHAPTERS.mkdir(parents=True, exist_ok=True)
    path = bt.CHAPTERS / filename
    n = 2
    while path.exists():
        path = bt.CHAPTERS / f"{Path(filename).stem}-{n}.md"
        n += 1
    path.write_text(text, encoding="utf-8")

    problems = bt.check(path)
    chapter = bt.parse(path)
    if problems:
        print("This chapter can't go in the book yet:\n- " + "\n- ".join(problems))
        path.unlink()
        sys.exit(1)

    print(f"\nChapter ready: {path}")
    print(f"  {chapter['title']}  ·  run by {chapter['run_by']}  ·  {chapter['words']:,} words")
    print(f"  Seed: {chapter['seed']}")
    print(f"\n{LICENCE}")

    if args.no_send or not sys.stdin.isatty():
        web_instructions(path)
        return
    if ask("Send it to the book now? [Y/n]: ", "y").lower() not in ("y", "yes"):
        web_instructions(path)
        return
    if not send_with_gh(path, chapter["title"]):
        web_instructions(path)


if __name__ == "__main__":
    main()
