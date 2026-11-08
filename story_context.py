"""
Story context — holds the working title for the current run and derives
all story-specific vault paths from it.

Call set_story() once at the top of any run script before importing agents
or tools that write to the vault. Tools check get_story() at call time and
dual-write to both the shared permanent location and the story folder.
"""

from pathlib import Path

import config

_VAULT = config.VAULT
_STORY_TITLE: str | None = None


def set_story(title: str) -> Path:
    global _STORY_TITLE
    _STORY_TITLE = title
    return ensure_story_dirs()


def get_story() -> str | None:
    return _STORY_TITLE


# ------------------------------------------------------------------ #
# Path helpers — return None if no story is set                       #
# ------------------------------------------------------------------ #

def story_dir() -> Path | None:
    return (_VAULT / "stories" / _STORY_TITLE) if _STORY_TITLE else None


def characters_dir() -> Path | None:
    d = story_dir()
    return (d / "characters") if d else None


def faces_dir() -> Path | None:
    d = story_dir()
    return (d / "faces") if d else None


def drafts_dir() -> Path | None:
    d = story_dir()
    return (d / "drafts") if d else None


def theory_deposits_dir() -> Path | None:
    d = story_dir()
    return (d / "theory_deposits") if d else None


def plots_dir() -> Path | None:
    d = story_dir()
    return (d / "plots") if d else None


def annotations_dir() -> Path | None:
    d = story_dir()
    return (d / "annotations") if d else None


def letters_dir() -> Path | None:
    d = story_dir()
    return (d / "letters") if d else None


# ------------------------------------------------------------------ #
# Permanent shared paths                                              #
# ------------------------------------------------------------------ #

PERMANENT_DEPOSITS   = _VAULT / "theory" / "deposits"


# ------------------------------------------------------------------ #
# Scaffold story folder on set_story()                                #
# ------------------------------------------------------------------ #

def ensure_story_dirs() -> Path | None:
    d = story_dir()
    if not d:
        return None
    for sub in ["characters", "faces", "drafts", "theory_deposits", "annotations", "plots", "letters"]:
        (d / sub).mkdir(parents=True, exist_ok=True)
    used_json = d / "faces" / "used.json"
    if not used_json.exists():
        used_json.write_text("[]")
    p = d / "seed.md"
    if not p.exists():
        p.write_text("# Seed\n\n")
    return d
