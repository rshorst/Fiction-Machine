"""
Per-narrative file tools — read and write to vault/stories/[title]/.
"""

import sys
import os
from pathlib import Path
from typing import Type

from pydantic import BaseModel, Field
from crewai.tools import BaseTool

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import story_context


class ReadDraftFileInput(BaseModel):
    filename: str = Field(
        description="Draft filename to read, e.g. 'em_aberto_draft_01.md'. "
                    "Reads from vault/stories/[story]/drafts/."
    )


class ReadDraftFileTool(BaseTool):
    name: str = "Read Draft File"
    description: str = (
        "Read a specific draft file from vault/stories/[story]/drafts/[filename]. "
        "Use this to read a previous draft version by name."
    )
    args_schema: Type[BaseModel] = ReadDraftFileInput

    def _run(self, filename: str) -> str:
        drafts = story_context.drafts_dir()
        if not drafts:
            return "No story set."
        if not filename.endswith(".md"):
            filename += ".md"
        path = drafts / filename
        if not path.exists():
            available = [p.name for p in drafts.glob("*.md")]
            return f"File '{filename}' not found. Available: {available}"
        try:
            return path.read_text()
        except OSError as e:
            return f"Error reading {path}: {e}"


class WriteDraftFileInput(BaseModel):
    filename: str = Field(
        description="Draft filename, e.g. 'draft_02.md'. Written to vault/stories/[story]/drafts/."
    )


class WriteDraftFileTool(BaseTool):
    name: str = "Write Draft File"
    description: str = (
        "Signal that the draft is complete. The filename you specify will be used as the "
        "destination in vault/stories/[story]/drafts/. Do NOT pass draft content as a "
        "parameter — for any draft over a few hundred words, produce the full draft text "
        "as your task's final output instead; the Task's output_file mechanism writes it "
        "to disk directly via Python file I/O. Call this tool only to confirm the filename."
    )
    args_schema: Type[BaseModel] = WriteDraftFileInput

    def _run(self, filename: str) -> str:
        drafts = story_context.drafts_dir()
        if not drafts:
            return "No story set — call story_context.set_story() before writing a draft file."
        if not filename.endswith(".md"):
            filename += ".md"
        path = drafts / filename
        if path.exists():
            try:
                return f"Draft file exists at {path} ({path.stat().st_size} bytes)."
            except OSError:
                return f"Draft file exists at {path}."
        return f"Draft will be written to {path} via task output_file."


class WriteCharacterFileInput(BaseModel):
    name: str = Field(description="Character filename without extension, e.g. 'vera_okafor'")
    content: str = Field(description="Full character profile content to write")


class WriteCharacterFileTool(BaseTool):
    name: str = "Write Character File"
    description: str = (
        "Write a character profile to vault/stories/[slug]/characters/[name].md. "
        "The content parameter MUST include ALL of the following, "
        "in this order: (1) face description — what you saw in the photograph, unresolved; "
        "(2) history — enough to fill a life, more than will appear in the story; "
        "(3) desire (stated) — what they would say they want; "
        "(4) desire (unstated) — what they actually want, which they may not know; "
        "(5) contradiction — the thing in them that doesn't fit; "
        "(6) what they don't know about themselves; "
        "(7) the COMPLETE interview transcript — every question asked, every answer given, "
        "every refusal, deflection, silence, and wrong-question answer recorded verbatim. "
        "The interview is the most important part. Do not summarise it. Do not omit questions. "
        "If they went silent, write: [silence]. If they refused, write what they said instead."
    )
    args_schema: Type[BaseModel] = WriteCharacterFileInput

    def _run(self, name: str, content: str) -> str:
        filename = name.lower().replace(" ", "_").strip("_") + ".md"
        body     = content.strip() + "\n"

        char_dir = story_context.characters_dir()
        if not char_dir:
            return "No story set — character file not written."
        try:
            char_dir.mkdir(parents=True, exist_ok=True)
            (char_dir / filename).write_text(body)
            return f"Character profile written to: {char_dir / filename}"
        except OSError as e:
            return f"Error writing character file {filename}: {e}"


class ReadAnnotationsFileInput(BaseModel):
    filename: str = Field(
        default="",
        description=(
            "Annotation filename to read from vault/stories/[story]/annotations/. "
            "E.g. 'sue_pen_annotations.md', 'richard_reading.md'. "
            "Leave blank to list all available annotation files."
        ),
    )


class ReadAnnotationsFileTool(BaseTool):
    name: str = "Read Annotations File"
    description: str = (
        "Read a specific annotation file from vault/stories/[story]/annotations/. "
        "Leave filename blank to list available files. "
        "Use this to read Sue Pen's marks, Richard's reading, or any other annotation."
    )
    args_schema: Type[BaseModel] = ReadAnnotationsFileInput

    def _run(self, filename: str = "") -> str:
        ann_dir = story_context.annotations_dir()
        if not ann_dir or not ann_dir.exists():
            return "No annotations directory found for current story."
        if not filename:
            files = sorted(ann_dir.glob("*.md"))
            if not files:
                return "No annotation files found."
            return "Available annotation files:\n" + "\n".join(f.name for f in files)
        if not filename.endswith(".md"):
            filename += ".md"
        path = ann_dir / filename
        if not path.exists():
            available = [f.name for f in sorted(ann_dir.glob("*.md"))]
            return f"File '{filename}' not found. Available: {available}"
        try:
            return path.read_text()
        except OSError as e:
            return f"Error reading {path}: {e}"


class WriteLetterFileInput(BaseModel):
    name: str = Field(description="Letter filename without extension, e.g. 'guha_note'")
    content: str = Field(description="Full content of the letter to write")


class WriteLetterFileTool(BaseTool):
    name: str = "Write Letter File"
    description: str = (
        "Write a letter or editor's note to vault/stories/[slug]/letters/[name].md. "
        "Pass the filename without extension as 'name' and the full text as 'content'."
    )
    args_schema: Type[BaseModel] = WriteLetterFileInput

    def _run(self, name: str, content: str) -> str:
        letters = story_context.letters_dir()
        if not letters:
            return "No story set — letter file not written."
        filename = name.lower().replace(" ", "_").strip("_") + ".md"
        path = letters / filename
        try:
            letters.mkdir(parents=True, exist_ok=True)
            path.write_text(content.strip() + "\n")
            return f"Letter written to: {path}"
        except OSError as e:
            return f"Error writing letter {filename}: {e}"
