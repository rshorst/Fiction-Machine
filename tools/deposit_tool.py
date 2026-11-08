"""
Deposit tool — writes a fragment into the miranda_papers ChromaDB collection
and mirrors it as a markdown file in two locations:
  1. vault/theory/deposits/           — permanent shared collection
  2. vault/stories/[title]/theory_deposits/  — story-specific (if story is set)
"""

import re
import sys
import os
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag import deposit, miranda_papers
import story_context

PERMANENT_DEPOSITS = story_context.PERMANENT_DEPOSITS
import config
MIRANDA_PAPERS     = config.MIRANDA_PAPERS
BIBLIOGRAPHY       = PERMANENT_DEPOSITS.parent / "bibliography.md"

_ARXIV_URL_RE      = re.compile(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5})', re.IGNORECASE)
_ARXIV_ID_RE       = re.compile(r'\barxiv:(\d{4}\.\d{4,5})(?:v\d+)?\b', re.IGNORECASE)
_PDF_URL_RE        = re.compile(r'https?://\S+\.pdf\b', re.IGNORECASE)


def _extract_arxiv_id(source: str, provenance: str) -> Optional[str]:
    """Return base arXiv ID (no version suffix) from source/provenance, or None."""
    for text in (source, provenance):
        m = _ARXIV_URL_RE.search(text) or _ARXIV_ID_RE.search(text)
        if m:
            return re.sub(r'v\d+$', '', m.group(1))
    return None


def _arxiv_year(arxiv_id: str) -> str:
    return str(2000 + int(arxiv_id[:2]))


def _source_title(source: str) -> str:
    """Strip leading 'arXiv:ID —' or 'deposit-from-reasoning_' prefix; return clean title."""
    s = re.sub(r'^arXiv:\S+\s*[—–-]+\s*', '', source).strip()
    if s.startswith('deposit-from-reasoning_'):
        s = s[len('deposit-from-reasoning_'):].replace('-', ' ').replace('_', ' ').title()
    return s or source


def _provenance_authors(provenance: str) -> str:
    """Heuristic: extract author string if provenance begins with 'Lastname, F.' pattern."""
    p = provenance.strip()
    if p.startswith(('http', 'arXiv:', '"')):
        return ''
    end = re.search(r'\s+"|\s+arXiv:|\s+\(20', p, re.IGNORECASE)
    if not end:
        return ''
    candidate = p[:end.start()].strip().rstrip('.,')
    if re.search(r'[A-Z][a-z]+,\s+[A-Z]\.', candidate) or re.search(r'et al\.?', candidate):
        return candidate
    return ''


def _update_bibliography(source: str, provenance: str, story: Optional[str]) -> None:
    """Append or update the bibliography entry for this deposit."""
    if not BIBLIOGRAPHY.exists() or not story:
        return

    arxiv_id = _extract_arxiv_id(source, provenance)
    bib = BIBLIOGRAPHY.read_text()

    if arxiv_id:
        id_re = re.compile(rf'\barXiv:{re.escape(arxiv_id)}(?:v\d+)?\b', re.IGNORECASE)
        m = id_re.search(bib)
        if m:
            # Entry exists — find its Engaged in: line within the same entry block.
            block_end_m = re.search(r'\n\n', bib, m.start())
            block_end   = block_end_m.start() if block_end_m else len(bib)
            em = re.search(r'Engaged in: ([^\n]+)', bib[m.start():block_end])
            if em:
                abs_start = m.start() + em.start()
                abs_end   = m.start() + em.end()
                slugs = [s.strip() for s in em.group(1).rstrip('.').split(',')]
                if story not in slugs:
                    slugs.append(story)
                    bib = bib[:abs_start] + f"Engaged in: {', '.join(slugs)}." + bib[abs_end:]
                    BIBLIOGRAPHY.write_text(bib)
        else:
            # New paper — append before the Reasoning Deposits section divider.
            authors = _provenance_authors(provenance)
            cite    = f"{authors}. arXiv:{arxiv_id} ({_arxiv_year(arxiv_id)})." if authors \
                      else f"arXiv:{arxiv_id} ({_arxiv_year(arxiv_id)})."
            entry   = f"\n**{_source_title(source)}**\n{cite}\nEngaged in: {story}.\n"
            marker  = "\n---\n\n## Reasoning"
            if marker not in bib:
                marker = "\n---\n\n## Theory"
            pos = bib.index(marker) if marker in bib else len(bib)
            BIBLIOGRAPHY.write_text(bib[:pos] + entry + bib[pos:])
    else:
        # Reasoning deposit — append before the Theory (non-arXiv) section divider.
        entry  = f"\n**{_source_title(source)}** *(reasoning deposit)*\nEngaged in: {story}.\n"
        marker = "\n---\n\n## Theory"
        pos    = bib.index(marker) if marker in bib else len(bib)
        BIBLIOGRAPHY.write_text(bib[:pos] + entry + bib[pos:])


def _try_download_pdf(source: str, provenance: str) -> str:
    pdf_url = paper_id = None

    for text in (provenance, source):
        m = _ARXIV_URL_RE.search(text)
        if m:
            paper_id = m.group(1)
            pdf_url  = f"https://arxiv.org/pdf/{paper_id}"
            break

    if not pdf_url:
        for text in (provenance, source):
            m = _ARXIV_ID_RE.search(text)
            if m:
                paper_id = m.group(1)
                pdf_url  = f"https://arxiv.org/pdf/{paper_id}"
                break

    if not pdf_url:
        m = _PDF_URL_RE.search(provenance)
        if m:
            pdf_url = m.group(0)

    if not pdf_url:
        return "(no PDF URL found in provenance — paper not saved)"

    filename = f"{paper_id + '_' if paper_id else ''}{_slug(source, 50)}.pdf"
    dest     = MIRANDA_PAPERS / filename

    if dest.exists():
        return f"(paper already at {dest})"

    try:
        MIRANDA_PAPERS.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(pdf_url, headers={"User-Agent": "unslop-research/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            dest.write_bytes(resp.read())
        return f"PDF saved to {dest}"
    except OSError as e:
        return f"(PDF download failed: {e})"


def _slug(s: str, maxlen: int = 60) -> str:
    return re.sub(r"[^\w-]", "_", s)[:maxlen].strip("_")


def _write_md(directory: Path, filename: str, md: str) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / filename).write_text(md)


class DepositInput(BaseModel):
    text: str = Field(description="The fragment, quote, or observation to deposit")
    source: str = Field(description="Short identifier for the source (e.g. paper title or URL slug)")
    provenance: str = Field(description="Where this came from — full citation, URL, or description")
    tags: Optional[List[str]] = Field(default=None, description="Optional tags, e.g. ['emergence', 'refusal', 'multimodal']")


class DepositTool(BaseTool):
    name: str = "Deposit to Corpus"
    description: str = (
        "Deposit a text fragment into the miranda_papers corpus. "
        "Use this to record a paper excerpt, observation, or anomaly you want to preserve. "
        "Provide the text, a short source identifier, its provenance (URL or citation), "
        "and optional tags."
    )
    args_schema: Type[BaseModel] = DepositInput

    def _run(
        self,
        text: str,
        source: str,
        provenance: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        story = story_context.get_story()

        # Attach story tag so deposits are traceable
        all_tags = list(tags or [])
        if story and story not in all_tags:
            all_tags.append(story)

        doc_id = deposit(
            collection=miranda_papers,
            text=text,
            source=source,
            provenance=provenance,
            tags=all_tags,
        )

        ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{_slug(source)}_{ts}.md"
        tag_str  = ", ".join(all_tags)
        md = (
            f"---\n"
            f"source: {source}\n"
            f"provenance: {provenance}\n"
            f"story: {story or 'unset'}\n"
            f"deposited: {datetime.now().isoformat()}\n"
            f"tags: [{tag_str}]\n"
            f"doc_id: {doc_id}\n"
            f"---\n\n"
            f"{text}\n"
        )

        # 1. Permanent shared collection
        _write_md(PERMANENT_DEPOSITS, filename, md)

        # 2. Story-specific collection (if a story is set)
        story_deposits = story_context.theory_deposits_dir()
        if story_deposits:
            _write_md(story_deposits, filename, md)

        locations = str(PERMANENT_DEPOSITS)
        if story_deposits:
            locations += f" + {story_deposits}"

        _update_bibliography(source, provenance, story)

        pdf_note = _try_download_pdf(source, provenance)
        return f"Deposited as {doc_id} ({miranda_papers.count()} documents in corpus). Written to: {locations}. {pdf_note}"
