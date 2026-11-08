#!/usr/bin/env python
"""
Check a pull request that adds a chapter to the book.
GitHub runs this on every pull request that touches book/chapters/.

Passes when the pull request adds exactly one new chapter file, changes
nothing else, and the chapter passes book_tools.check().

Usage:
    python validate_chapter.py --base origin/main
"""

import argparse
import subprocess
import sys

import book_tools as bt


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="origin/main", help="Branch the pull request goes into")
    args = ap.parse_args()

    diff = subprocess.run(["git", "diff", "--name-status", f"{args.base}...HEAD"],
                          capture_output=True, text=True, check=True).stdout.split("\n")
    changes = [line.split("\t") for line in diff if line.strip()]
    problems = []
    added = [p for s, *rest in changes for p in rest[-1:] if s == "A" and p.startswith("book/chapters/") and p.endswith(".md")]
    others = [rest[-1] for s, *rest in changes if rest and rest[-1] not in added]

    if len(added) != 1:
        problems.append(f"A chapter pull request adds exactly one file to book/chapters/ (this one adds {len(added)}).")
    if others:
        problems.append("A chapter pull request changes nothing else. Also changed: " + ", ".join(others))
    for path in added:
        problems += [f"{path}: {p}" for p in bt.check(path)]

    if problems:
        print("This chapter can't go in the book yet:\n- " + "\n- ".join(problems))
        sys.exit(1)
    c = bt.parse(added[0])
    print(f"OK: '{c['title']}', run by {c['run_by']}, {c['words']:,} words. Ready for Rachel to read.")


if __name__ == "__main__":
    main()
