#!/usr/bin/env python
"""
Build the book from book/chapters/ into site/:

    site/index.html               the book to read online
    site/diagram.html             how the machine works
    site/fiction-machine-book.pdf the whole book, free to download

Needs pandoc, and Chrome or Chromium for the PDF. GitHub runs this after
every change to the book and publishes site/ with GitHub Pages.

Usage:
    python build_book.py
"""

import datetime
import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import book_tools as bt
import config

REPO = "https://github.com/rshorst/Fiction-Machine"
BOOK = bt.ROOT / "book"
SITE = bt.ROOT / "site"
PDF_NAME = "fiction-machine-book.pdf"


def md_to_html(md: str) -> str:
    return subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "html5", "--wrap=none"],
        input=md, capture_output=True, text=True, check=True,
    ).stdout


def long_date(iso: str) -> str:
    d = datetime.date.fromisoformat(iso)
    return f"{d.day} {d:%B %Y}"


def page(fragment: str) -> str:
    """Wrap a page fragment in a full HTML document."""
    return (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">\n'
        "<style>:root{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}"
        "body{margin:0}img{max-width:100%}[hidden]{display:none!important}</style>\n"
        f"</head>\n<body>\n{fragment}\n</body>\n</html>\n"
    )


def build_site(chapters, updated) -> None:
    data = {
        "updated": long_date(updated),
        "chapters": [
            {
                "title": c["title"], "run_by": c["run_by"], "seed": c["seed"],
                "date": long_date(c["made"]), "model": c["model"], "system": c["system"],
                "designer": c.get("designed_by", "Rachel Horst"), "words": c["words"],
                "html": md_to_html(c["body"]),
            }
            for c in chapters
        ],
    }
    t = (BOOK / "templates" / "site.html").read_text(encoding="utf-8")
    t = t.replace("__CHAPTERS__", json.dumps(data).replace("</", "<\\/")).replace("__REPO__", REPO)
    (SITE / "index.html").write_text(page(t), encoding="utf-8")
    (SITE / "diagram.html").write_text(page((BOOK / "diagram.html").read_text(encoding="utf-8")), encoding="utf-8")
    (SITE / ".nojekyll").write_text("")


def build_pdf(chapters, updated) -> bool:
    chrome = config.chrome_path()
    if not chrome:
        print("PDF skipped: Chrome or Chromium not found (set CHROME_PATH).")
        return False
    e = html.escape
    total = sum(c["words"] for c in chapters)
    parts = [
        '<section class="title"><h1>The Fiction Machine</h1>'
        f"<p>{len(chapters)} stories made by the Fiction Machine (unslop.), designed by Rachel Horst.</p>"
        f'<p class="small">Edition of {e(long_date(updated))} · {total:,} words · {REPO}</p></section>',
        '<section class="toc"><h2>Contents</h2><ol>'
        + "".join(
            f'<li><span class="n">{i:02d}</span><span><span class="t">{e(c["title"])}</span>'
            f'<span class="r">{e(long_date(c["made"]))}</span></span></li>'
            for i, c in enumerate(chapters, 1)
        )
        + "</ol></section>",
    ]
    for i, c in enumerate(chapters, 1):
        parts.append(
            f'<section class="chapter"><div class="num">Chapter {i}</div><h2>{e(c["title"])}</h2>'
            f'<div class="story">{md_to_html(c["body"])}</div>'
            '<div class="note"><dl>'
            f'<dt>Made</dt><dd>{e(long_date(c["made"]))}</dd>'
            f'<dt>Run by</dt><dd>{e(c["run_by"])}</dd>'
            f'<dt>Seed</dt><dd>{e(c["seed"])}</dd>'
            f'<dt>System</dt><dd>{e(c["system"])}, designed by {e(c.get("designed_by", "Rachel Horst"))}</dd>'
            f'<dt>Model</dt><dd class="mono">{e(c["model"])}</dd>'
            f'<dt>Length</dt><dd>{c["words"]:,} words</dd>'
            "</dl></div></section>"
        )
    parts.append(
        '<section class="colophon"><h2>Colophon</h2>'
        "<p>The Fiction Machine (unslop.) is a multi-agent fiction system designed by Rachel Horst in April 2026. "
        "Each chapter began as one seed sentence and was researched, drafted, annotated, revised and cut by its agents.</p>"
        "<p>Each chapter is © the person who ran the machine and is shared under the Creative Commons "
        "Attribution-NonCommercial 4.0 licence (CC BY-NC 4.0). The code is under the MIT licence.</p>"
        f"<p>Read online, see how the machine works, or add a chapter: {REPO}</p></section>"
    )
    doc = (BOOK / "templates" / "print.html").read_text(encoding="utf-8").replace("__BODY__", "\n".join(parts))
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "book.html"
        src.write_text(doc, encoding="utf-8")
        out = SITE / PDF_NAME
        subprocess.run(
            [chrome, "--headless=new", "--no-sandbox", "--disable-gpu", "--run-all-compositor-stages-before-draw",
             "--virtual-time-budget=10000", f"--print-to-pdf={out}", "--no-pdf-header-footer", str(src)],
            check=True, capture_output=True,
        )
    return True


def main() -> None:
    chapters = bt.all_chapters()
    bad = {c["file"]: bt.check(bt.CHAPTERS / c["file"]) for c in chapters}
    bad = {k: v for k, v in bad.items() if v}
    if bad:
        for name, problems in bad.items():
            print(f"{name}: " + "; ".join(problems))
        sys.exit("Fix the chapters above, then build again.")
    if not chapters:
        sys.exit("No chapters in book/chapters/.")
    SITE.mkdir(exist_ok=True)
    updated = max(c.get("added", c["made"]) for c in chapters)
    build_site(chapters, updated)
    made_pdf = build_pdf(chapters, updated)
    print(f"Built {len(chapters)} chapters into {SITE}/" + (f" with {PDF_NAME}" if made_pdf else " (no PDF)"))


if __name__ == "__main__":
    main()
