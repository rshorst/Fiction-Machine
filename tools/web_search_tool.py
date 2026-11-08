"""
DuckDuckGo web search tool — no API key required, no OpenAI dependency.
"""

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from ddgs import DDGS


class WebSearchInput(BaseModel):
    query: str = Field(description="Search query")
    max_results: int = Field(default=5, description="Number of results to return")


class DuckDuckGoSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = (
        "Search the web using DuckDuckGo. Returns titles, URLs, and snippets. "
        "Use this to find recent papers, articles, and ideas."
    )
    args_schema: Type[BaseModel] = WebSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        results = list(DDGS().text(query, max_results=max_results))
        if not results:
            return "No results found."
        lines = []
        for r in results:
            lines.append(f"Title: {r.get('title', '')}")
            lines.append(f"URL: {r.get('href', '')}")
            lines.append(f"Snippet: {r.get('body', '')}")
            lines.append("")
        return "\n".join(lines).strip()
