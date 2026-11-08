"""
RAG tools — reach into the two ChromaDB collections.
Two separate tools so agents are explicit about which corpus they are drawing from.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Type
from pydantic import BaseModel, Field
from crewai.tools import BaseTool

from rag import reach, miranda_papers, voices


def _format_results(results: dict) -> str:
    docs = results.get("documents", [[]])[0]
    metas = results.get("metadatas", [[]])[0]
    if not docs:
        return "Nothing found."
    lines = []
    for doc, meta in zip(docs, metas):
        source = meta.get("source", "unknown")
        provenance = meta.get("provenance", "")
        lines.append(f"[{source}]")
        if provenance:
            lines.append(f"  ({provenance})")
        lines.append(f"  {doc.strip()}")
        lines.append("")
    return "\n".join(lines).strip()


class ReachInput(BaseModel):
    query: str = Field(description="What to reach for — a theme, image, question, or phrase")
    n: int = Field(default=3, description="Number of fragments to retrieve (1-6)")


class ReachMirandaTool(BaseTool):
    name: str = "Reach into Miranda's Papers"
    description: str = (
        "Retrieve fragments from miranda_papers — theory, research, anomalies, "
        "provocations that Miranda deposited before the draft existed. "
        "Use a query that reaches for a theme, image, or unresolved question."
    )
    args_schema: Type[BaseModel] = ReachInput

    def _run(self, query: str, n: int = 3) -> str:
        results = reach(miranda_papers, query, n=min(n, 6))
        return _format_results(results)


class ReachVoicesTool(BaseTool):
    name: str = "Reach into Voices"
    description: str = (
        "Retrieve fragments from the voices corpus — Rachel's writing, "
        "the particular way she sees, opinion and commitment. "
        "Use a query that reaches for a feeling, a register, a way of noticing."
    )
    args_schema: Type[BaseModel] = ReachInput

    def _run(self, query: str, n: int = 3) -> str:
        results = reach(voices, query, n=min(n, 6))
        return _format_results(results)
