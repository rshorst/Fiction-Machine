#!/usr/bin/env python
"""
Build the book from book/chapters/ into site/:

    site/index.html               the book to read online
    site/diagram.html             how the machine works
    site/contribute.html          how to run the machine and add a chapter
    site/warm-prior.pdf           the whole book, free to download

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
PDF_NAME = "warm-prior.pdf"


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


CONTRIBUTE_SECTIONS = ["What it costs", "Setup", "Run it", "Where the output lands",
                       "Faces and Unsplash", "Add your story to the book", "Licence"]


def build_contribute() -> None:
    """contribute.html: the README's steps for running the machine and adding a chapter."""
    import re
    readme = (bt.ROOT / "README.md").read_text(encoding="utf-8")
    sections = dict(re.findall(r"^## (.+?)\n(.*?)(?=^## |\Z)", readme, re.S | re.M))
    missing = [h for h in CONTRIBUTE_SECTIONS if h not in sections]
    if missing:
        sys.exit(f"README.md is missing sections used by contribute.html: {', '.join(missing)}")
    md = "\n\n".join(f"## {h}\n\n{sections[h].strip()}" for h in CONTRIBUTE_SECTIONS)
    body = subprocess.run(["pandoc", "-f", "gfm", "-t", "html5", "--wrap=none", "--no-highlight"],
                          input=md, capture_output=True, text=True, check=True).stdout
    # Links that point at files in the repo go to GitHub; tables scroll on small screens.
    body = re.sub(r'href="(?!https?:|#|mailto:)([^"]+)"', lambda m: f'href="{REPO}/blob/main/{m.group(1)}"', body)
    body = body.replace("<table>", '<div class="table-wrap"><table>').replace("</table>", "</table></div>")
    t = (BOOK / "templates" / "page.html").read_text(encoding="utf-8")
    t = (t.replace("__TITLE__", "How to add a chapter")
          .replace("__LEDE__", "Run the machine on a seed of your own, then send your finished story in. "
                               "Rachel Horst reads every chapter before it joins the book.")
          .replace("__BODY__", body).replace("__REPO__", REPO))
    (SITE / "contribute.html").write_text(page(t), encoding="utf-8")


def build_pdf(chapters, updated) -> bool:
    chrome = config.chrome_path()
    if not chrome:
        print("PDF skipped: Chrome or Chromium not found (set CHROME_PATH).")
        return False
    e = html.escape
    total = sum(c["words"] for c in chapters)
    parts = [
        '<section class="title"><h1>Warm Prior</h1><p class="sub">Stories from a Fiction Machine</p>'
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
    set_outline(out, chapters)
    return True


def set_outline(pdf: Path, chapters) -> None:
    """Replace any bookmarks Chrome made with one per story: Contents, each title, Colophon."""
    try:
        import pymupdf
    except ImportError:
        print("Bookmarks skipped: pip install pymupdf to add them.")
        return
    doc = pymupdf.open(str(pdf))
    pages = [doc[i].get_text().lower() for i in range(doc.page_count)]

    def first_page(marker, start=0):
        for i in range(start, len(pages)):
            if marker in pages[i]:
                return i
        return None

    toc, at = [], first_page("contents")
    if at is not None:
        toc.append([1, "Contents", at + 1])
    for n, c in enumerate(chapters, 1):
        p = first_page(f"chapter {n}\n", (at or 0) + 1)
        if p is not None:
            toc.append([1, c["title"], p + 1])
            at = p
    col = first_page("colophon", (at or 0) + 1)
    if col is not None:
        toc.append([1, "Colophon", col + 1])
    doc.set_toc(toc)
    tmp = pdf.with_suffix(".tmp.pdf")
    doc.save(str(tmp), garbage=3, deflate=True)
    doc.close()
    tmp.replace(pdf)


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
    build_contribute()
    made_pdf = build_pdf(chapters, updated)
    print(f"Built {len(chapters)} chapters into {SITE}/" + (f" with {PDF_NAME}" if made_pdf else " (no PDF)"))


if __name__ == "__main__":
    main()
