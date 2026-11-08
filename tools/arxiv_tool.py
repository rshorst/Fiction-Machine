"""
Resilient arXiv search tool. Wraps ArxivPaperTool with a shorter timeout and an
actionable error message so Miranda knows to try web search or deposit from reasoning
rather than stalling when the arXiv API is rate-limited or unreachable.
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

ATOM = "{http://www.w3.org/2005/Atom}"
API_URL = "http://export.arxiv.org/api/query"
TIMEOUT = 8  # seconds — fail fast rather than hanging the crew

UNAVAILABLE = (
    "arXiv search unavailable (timeout or rate limit). "
    "Switch to Web Search for this query, or deposit a fragment from your own "
    "reasoning using the Deposit to Corpus tool. Do not stop — keep going."
)


class ArxivInput(BaseModel):
    search_query: str = Field(description="arXiv search query string")
    max_results: int = Field(default=3, description="Number of results to return")


class ResilientArxivTool(BaseTool):
    name: str = "arXiv Search"
    description: str = (
        "Search arXiv for papers. Use specific, unusual query terms — not 'survey of' "
        "or 'benchmark'. If unavailable, the tool will tell you and you should use "
        "Web Search or deposit from your own reasoning instead."
    )
    args_schema: Type[BaseModel] = ArxivInput

    def _run(self, search_query: str, max_results: int = 3) -> str:
        url = f"{API_URL}?search_query={urllib.parse.quote(search_query)}&start=0&max_results={max_results}"
        try:
            with urllib.request.urlopen(url, timeout=TIMEOUT) as resp:
                if resp.status == 429:
                    return UNAVAILABLE
                raw = resp.read()
        except OSError:
            return UNAVAILABLE

        try:
            root = ET.fromstring(raw)
        except ET.ParseError:
            return UNAVAILABLE

        entries = root.findall(f"{ATOM}entry")
        if not entries:
            return f"No arXiv results for: {search_query}"

        lines = []
        for entry in entries:
            title   = (entry.findtext(f"{ATOM}title") or "").strip().replace("\n", " ")
            summary = (entry.findtext(f"{ATOM}summary") or "").strip().replace("\n", " ")[:300]
            link    = next(
                (l.get("href") for l in entry.findall(f"{ATOM}link") if l.get("type") == "text/html"),
                ""
            )
            lines.append(f"Title: {title}\nURL: {link}\nAbstract: {summary}...\n")

        return "\n".join(lines).strip()
