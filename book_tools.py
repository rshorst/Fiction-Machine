"""
What a chapter of the book is, shared by submit_chapter.py, validate_chapter.py
and build_book.py.

A chapter is one markdown file in book/chapters/:

    ---
    title: Warm Prior
    run_by: Rachel Horst
    seed: Someone in Vancouver is sent voice messages by ...
    made: 2026-04-27
    model: claude-opus-4-7
    system: unslop.
    designed_by: Rachel Horst
    added: 2026-11-08
    ---
    The story, in markdown, without its title line or the machine's footer.
"""

import datetime
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CHAPTERS = ROOT / "book" / "chapters"
FIELDS = ["title", "run_by", "seed", "made", "model", "system", "designed_by", "added"]
REQUIRED = ["title", "run_by", "seed", "made", "model", "system"]
MIN_WORDS, MAX_WORDS = 1000, 15000


def slugify(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return s[:50] or "chapter"


def parse(path) -> dict:
    """Read a chapter file into a dict with 'body' and 'words'."""
    text = Path(path).read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        raise ValueError("The file must start with a --- block of chapter details.")
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    meta["body"] = m.group(2).strip()
    meta["words"] = len(meta["body"].split())
    meta["file"] = Path(path).name
    return meta


def from_draft(draft_path, run_by: str, made: str | None = None, added: str | None = None) -> tuple[str, str]:
    """
    Turn a finished draft_03.md into chapter text.
    Returns (suggested_filename, chapter_text).
    """
    md = Path(draft_path).read_text(encoding="utf-8")
    body, sep, foot = md.rpartition("\n---\n")
    if not sep:
        raise ValueError(f"{draft_path} has no machine note at the end. Is it a finished draft_03.md?")
    note = dict(
        (k.strip().lower().replace(" ", "_"), v.strip())
        for k, v in re.findall(r"^([A-Za-z][A-Za-z ]*?):\s*(.+?)\s*$", foot, re.M)
    )
    m = re.match(r"\s*#\s*(.+)\n", body)
    if not m:
        raise ValueError(f"{draft_path} does not start with a # Title line.")
    title = m.group(1).strip()
    story = body[m.end():].strip()

    if not made:
        made = datetime.date.fromtimestamp(Path(draft_path).stat().st_mtime).isoformat()
    meta = {
        "title": title,
        "run_by": run_by.strip(),
        "seed": " ".join(note.get("seed", "").split()),
        "made": made,
        "model": note.get("models", note.get("model", "")),
        "system": note.get("system", "unslop.").rstrip(),
        "designed_by": re.sub(r"\s*\(.*\)", "", note.get("designed_by", "Rachel Horst")),
        "added": added or datetime.date.today().isoformat(),
    }
    head = "\n".join(f"{k}: {meta[k]}" for k in FIELDS)
    return f"{slugify(title)}.md", f"---\n{head}\n---\n\n{story}\n"


def check(path) -> list[str]:
    """Problems with one chapter file; an empty list means it passes."""
    try:
        c = parse(path)
    except (ValueError, UnicodeDecodeError) as e:
        return [str(e)]
    problems = [f"Missing '{k}' in the chapter details." for k in REQUIRED if not c.get(k)]
    if c.get("system", "").rstrip(".") != "unslop":
        problems.append("The chapter must come from the Fiction Machine (system: unslop.).")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", c.get("made", "")):
        problems.append("'made' must be a date like 2026-11-08.")
    if not (MIN_WORDS <= c["words"] <= MAX_WORDS):
        problems.append(f"The story is {c['words']} words; chapters are {MIN_WORDS:,} to {MAX_WORDS:,} words.")
    if re.search(r"<\s*(script|iframe|object|embed|style)\b", c["body"], re.I):
        problems.append("The story contains HTML that isn't allowed (script, iframe, style).")
    if len(c.get("run_by", "")) > 80 or len(c.get("title", "")) > 120:
        problems.append("The name or title is too long.")
    return problems


def all_chapters() -> list[dict]:
    """Every chapter, in the order it was added to the book."""
    chs = [parse(p) for p in sorted(CHAPTERS.glob("*.md"))]
    return sorted(chs, key=lambda c: (c.get("added", ""), c.get("made", ""), c["file"]))
