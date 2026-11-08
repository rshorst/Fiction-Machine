"""
Convert a markdown draft to PDF via pandoc (HTML) + Chrome headless.
"""

import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

import config

CSS = """\
@import url('https://fonts.googleapis.com/css2?family=EB+Garamond:ital,wght@0,400;0,500;1,400&display=swap');

*, *::before, *::after { box-sizing: border-box; }

@page {
    size: letter;
    margin: 3cm 3.5cm;
}

body {
    font-family: 'EB Garamond', Georgia, 'Times New Roman', serif;
    font-size: 13pt;
    line-height: 1.7;
    color: #1a1a1a;
    max-width: 34em;
    margin: 0 auto;
}

h1 {
    font-size: 17pt;
    font-weight: 500;
    font-style: normal;
    letter-spacing: 0.01em;
    margin: 0 0 3em 0;
}

p {
    margin: 0;
    text-indent: 1.5em;
}

p:first-of-type { text-indent: 0; }
h1 + p          { text-indent: 0; }

hr {
    border: none;
    border-top: 1px solid #bbb;
    margin: 2.5em 0;
}

hr:last-of-type ~ p {
    font-family: 'Courier New', Courier, monospace;
    font-size: 8.5pt;
    line-height: 1.5;
    color: #666;
    text-indent: 0;
}
"""


def make_pdf(md_path: Path, pdf_path: Optional[Path] = None) -> None:
    md_path = Path(md_path)
    if pdf_path is not None:
        pdf_path = Path(pdf_path)
    if pdf_path is None:
        slug = md_path.parent.parent.name  # vault/stories/[slug]/drafts/draft_03.md
        pdf_path = md_path.parent / f"{slug}.pdf"

    chrome = config.chrome_path()
    missing = [n for n, ok in (("pandoc", shutil.which("pandoc")), ("Chrome/Chromium", chrome)) if not ok]
    if missing:
        print(f"PDF    : skipped ({' and '.join(missing)} not found; set CHROME_PATH in .env). "
              f"The story is in {md_path}")
        return

    with tempfile.TemporaryDirectory() as tmp:
        css_file  = Path(tmp) / "story.css"
        html_file = Path(tmp) / "story.html"
        css_file.write_text(CSS)

        subprocess.run(
            [
                "pandoc", str(md_path),
                "--standalone",
                "--to", "html5",
                f"--css={css_file}",
                "--embed-resources",
                "-o", str(html_file),
            ],
            check=True, capture_output=True,
        )

        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--no-sandbox",
                "--disable-gpu",
                "--run-all-compositor-stages-before-draw",
                f"--print-to-pdf={pdf_path.resolve()}",
                "--no-pdf-header-footer",
                str(html_file.resolve()),
            ],
            check=True, capture_output=True,
        )

    print(f"PDF    : {pdf_path}")
