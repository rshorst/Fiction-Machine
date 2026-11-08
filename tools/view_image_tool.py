"""
Vision tool — passes a local image to Claude Sonnet and returns what it sees.
Used by Frances to look at each portrait face directly before building a character.
"""

import base64
import io
from pathlib import Path
from typing import Type

from PIL import Image
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from utils.retry import completion_with_retry
import config

MAX_PX = 1000  # longest side before encoding


class ViewImageInput(BaseModel):
    image_path: str = Field(description="Absolute or relative path to the image file")
    prompt: str = Field(
        default=(
            "Look at this face carefully. Describe what you see: age, expression, "
            "the quality of attention in the eyes, how the person holds themselves, "
            "what they seem to be thinking. What is the first thing you notice? "
            "What do you notice second, only after you've been looking a while? "
            "What is unresolved in this face?"
        ),
        description="What to ask about the image"
    )


class ViewImageTool(BaseTool):
    name: str = "View Image"
    description: str = (
        "Look at an image file using Claude's vision. Pass a file path and an optional "
        "prompt. Returns a detailed description of what the image shows. "
        "Use this to examine portrait photographs before building characters from them."
    )
    args_schema: Type[BaseModel] = ViewImageInput

    def _run(self, image_path: str, prompt: str = "") -> str:
        path = Path(image_path)
        if not path.exists():
            return f"Image not found: {image_path}"

        if not prompt:
            prompt = (
                "Look at this face carefully. Describe what you see: age, expression, "
                "the quality of attention in the eyes, how the person holds themselves, "
                "what they seem to be thinking. What is the first thing you notice? "
                "What do you notice second, only after you've been looking a while? "
                "What is unresolved in this face?"
            )

        img = Image.open(path).convert("RGB")
        w, h = img.size
        if max(w, h) > MAX_PX:
            scale = MAX_PX / max(w, h)
            img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)

        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=85)
        b64 = base64.standard_b64encode(buf.getvalue()).decode()
        mime = "image/jpeg"

        resp = completion_with_retry(
            model=config.VISION_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url",
                     "image_url": {"url": f"data:{mime};base64,{b64}"}},
                    {"type": "text", "text": prompt},
                ],
            }],
            max_tokens=800,
        )
        return resp.choices[0].message.content
