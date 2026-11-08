"""
Annotation tool — Sue Pen writes her reading marks to
vault/stories/[story]/annotations.md (if story is set) or
vault/annotations/unsorted.md as fallback.

Appends only. The residue of attention accumulates.
"""

import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import story_context

import config
_FALLBACK = config.VAULT / "annotations" / "unsorted.md"


class WriteAnnotationsInput(BaseModel):
    content: str = Field(
        description=(
            "Annotations to append. Quote specific sentences, then mark what they are doing. "
            "Note what is performing and what is being. Note what should go and what should stay."
        )
    )


class WriteAnnotationsTool(BaseTool):
    name: str = "Write Annotations"
    description: str = (
        "Append reading marks to the story annotations file "
        "(vault/stories/[story]/annotations.md). "
        "Quote sentences. Mark what is performing versus being. "
        "Note what earns its form and what is reaching. "
        "Also note what is doing real work and should stay."
    )
    args_schema: Type[BaseModel] = WriteAnnotationsInput

    def _run(self, content: str) -> str:
        story_dir = story_context.story_dir()
        if story_dir:
            path = story_dir / "annotations.md"
        else:
            _FALLBACK.parent.mkdir(parents=True, exist_ok=True)
            path = _FALLBACK

        existing = path.read_text() if path.exists() else "# Annotations\n\n"
        ts  = datetime.now().strftime("%Y-%m-%d %H:%M")
        sep = "\n\n---\n\n" if existing.strip() and not existing.strip().endswith("---") else "\n"
        path.write_text(existing.rstrip() + sep + f"*Sue Pen — {ts}*\n\n" + content.strip() + "\n")

        return f"Annotations written to {path}."
