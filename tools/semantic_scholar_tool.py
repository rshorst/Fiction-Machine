"""
Semantic Scholar search tool for Miranda.

Used for theory, STS, philosophy of mind, education, postdigital studies,
sociotechnical imaginaries, cognitive science, cultural studies — fields where
arXiv coverage is thin.

Filters for open-access papers only. License is verified before returning:
CC-BY and CC-BY-NC variants are acceptable. Standard copyright is excluded.
Papers with open-access status but no declared license are returned with a caveat.
"""

import json
import time
import urllib.parse
import urllib.request
from typing import Type

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

API_URL = "https://api.semanticscholar.org/graph/v1/paper/search"
FIELDS = "paperId,title,abstract,year,openAccessPdf,isOpenAccess,externalIds,publicationTypes"
TIMEOUT = 12
# Polite delay — S2 unauthenticated limit is ~1 req/s
_RATE_DELAY = 1.2

UNAVAILABLE = (
    "Semantic Scholar search unavailable (timeout or rate limit). "
    "Try arXiv Search instead, or deposit a fragment from your own reasoning. "
    "Do not stop — keep going."
)

# Acceptable license prefixes (case-insensitive match against start of license string)
_OK_PREFIXES = (
    "cc by",       # CC BY, CC BY 4.0, CC BY 2.0, etc.
    "cc-by",       # alternate hyphen form
)
# NC variants are also acceptable
_OK_NC_PREFIXES = (
    "cc by-nc",
    "cc-by-nc",
)


def _license_ok(license_str: str) -> tuple[bool, str]:
    """
    Returns (acceptable, normalized_note).
    Empty/null license on an OA paper is allowed with a caveat.
    """
    s = (license_str or "").strip()
    if not s:
        return True, "open access — license unspecified"
    sl = s.lower()
    for p in _OK_PREFIXES + _OK_NC_PREFIXES:
        if sl.startswith(p):
            return True, s
    return False, f"excluded — license: {s}"


def _format_paper(paper: dict) -> str | None:
    """Return a formatted string for a paper, or None if it should be excluded."""
    if not paper.get("isOpenAccess"):
        return None

    oa_pdf = paper.get("openAccessPdf") or {}
    ok, license_note = _license_ok(oa_pdf.get("license") or "")
    if not ok:
        return None

    title    = (paper.get("title") or "").strip()
    year     = paper.get("year") or "n.d."
    abstract = (paper.get("abstract") or "").strip().replace("\n", " ")[:300]
    ext      = paper.get("externalIds") or {}
    arxiv_id = ext.get("ArXiv")
    doi      = ext.get("DOI")
    pdf_url  = oa_pdf.get("url") or ""
    pub_types = ", ".join(paper.get("publicationTypes") or [])

    id_line = (
        f"arXiv:{arxiv_id}" if arxiv_id
        else f"DOI:{doi}" if doi
        else f"S2:{paper.get('paperId', '')}"
    )

    parts = [
        f"Title: {title}",
        f"ID: {id_line}",
        f"Year: {year}",
        f"License: {license_note}",
    ]
    if pub_types:
        parts.append(f"Type: {pub_types}")
    if pdf_url:
        parts.append(f"PDF: {pdf_url}")
    parts.append(f"Abstract: {abstract}...")
    return "\n".join(parts)


class SemanticScholarInput(BaseModel):
    search_query: str = Field(description="Search query string")
    max_results: int = Field(default=3, description="Maximum results to return (capped at 5)")


class SemanticScholarTool(BaseTool):
    name: str = "Semantic Scholar Search"
    description: str = (
        "Search Semantic Scholar for open-access papers in theory, STS, philosophy of mind, "
        "education, postdigital studies, sociotechnical imaginaries, cognitive science, "
        "cultural studies. Returns CC-BY and CC-BY-NC papers only — license is verified. "
        "Use arXiv Search for technical AI/ML papers."
    )
    args_schema: Type[BaseModel] = SemanticScholarInput

    def _run(self, search_query: str, max_results: int = 3) -> str:
        max_results = min(max_results, 5)
        time.sleep(_RATE_DELAY)

        params = urllib.parse.urlencode({
            "query": search_query,
            "fields": FIELDS,
            "limit": max_results * 4,  # over-fetch; many will be filtered out
        })
        url = f"{API_URL}?{params}"

        try:
            req = urllib.request.Request(
                url, headers={"User-Agent": "unslop-research/1.0 (academic use)"}
            )
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                if resp.status == 429:
                    return UNAVAILABLE
                raw = resp.read()
        except OSError:
            return UNAVAILABLE

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return UNAVAILABLE

        if "message" in data and "429" in str(data.get("code", "")):
            return UNAVAILABLE

        papers = data.get("data") or []
        if not papers:
            return f"No Semantic Scholar results for: {search_query}"

        results = []
        for paper in papers:
            if len(results) >= max_results:
                break
            formatted = _format_paper(paper)
            if formatted:
                results.append(formatted)

        if not results:
            return (
                f"No open-access CC-licensed papers found for: {search_query}. "
                "Results exist but were excluded (standard copyright or no OA version). "
                "Try different terms, or use arXiv Search."
            )

        return "\n\n".join(results)
