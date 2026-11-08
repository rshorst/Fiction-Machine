"""
Settings for the Fiction Machine.

Every path the system reads or writes comes from here. Data lives under one
base folder, UNSLOP_HOME, which defaults to this repo. Set it in .env (or your
shell) to keep your vault, database and face library somewhere else.

Values are read from the environment first, then from a .env file in the repo.
"""

import os
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ENV_FILE = ROOT / ".env"


def _load_env_file() -> None:
    """Read KEY=VALUE lines from .env without overriding the real environment."""
    if not ENV_FILE.exists():
        return
    for line in ENV_FILE.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key.strip(), value)


_load_env_file()

# CrewAI and ChromaDB send anonymous usage telemetry by default. This machine
# opts out of both. Set them back in .env to opt in.
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("OTEL_SDK_DISABLED", "true")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")  # ChromaDB

# ── Paths ────────────────────────────────────────────────────────────
HOME = Path(os.environ.get("UNSLOP_HOME") or ROOT).expanduser().resolve()

SKILLS         = ROOT / "skills"          # prompt files ship with the code
VAULT          = HOME / "vault"           # stories, agent notes, theory, your writing
CHROMA_DIR     = HOME / "chromadb"        # rebuilt by ingest.py, never committed
FACES_DIR      = HOME / "faces"           # portrait library Frances draws from
MIRANDA_PAPERS = HOME / "miranda_papers"  # PDFs Miranda downloads during runs
OUTPUTS        = HOME / "outputs"         # token and cost log

# ── Models ───────────────────────────────────────────────────────────
# The machine was built and run on Opus. A cheaper model is fine for trying
# it out, but the stories will be different.
MODEL        = os.environ.get("UNSLOP_MODEL", "anthropic/claude-opus-4-7")
VISION_MODEL = os.environ.get("UNSLOP_VISION_MODEL", "anthropic/claude-sonnet-4-6")
SLUG_MODEL   = os.environ.get("UNSLOP_SLUG_MODEL", "claude-haiku-4-5-20251001")


# ── PDF ──────────────────────────────────────────────────────────────
def chrome_path() -> str | None:
    """Chrome or Chromium for printing the story PDF, or None if not found."""
    if os.environ.get("CHROME_PATH"):
        return os.environ["CHROME_PATH"]
    mac = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if Path(mac).exists():
        return mac
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome"):
        found = shutil.which(name)
        if found:
            return found
    return None


# ── API key ──────────────────────────────────────────────────────────
def ensure_api_key(name: str = "ANTHROPIC_API_KEY", why: str = "to run the agents") -> None:
    """
    Make sure an API key is set. If not, ask for it once (hidden input) and
    offer to save it to .env, which is in .gitignore and never committed.
    """
    if os.environ.get(name):
        return
    if not sys.stdin.isatty():
        raise SystemExit(f"{name} is not set. Add it to .env (see .env.example) {why}.")

    import getpass
    print(f"\n{name} is not set. You need one {why}.")
    key = getpass.getpass(f"Paste your {name} (input is hidden): ").strip()
    if not key:
        raise SystemExit("No key entered. Stopping.")
    os.environ[name] = key

    answer = input("Save it to .env in this folder for next time? [Y/n]: ").strip().lower()
    if answer in ("", "y", "yes"):
        with open(ENV_FILE, "a") as f:
            f.write(f"\n{name}={key}\n")
        try:
            ENV_FILE.chmod(0o600)
        except OSError:
            pass
        print(f"Saved to {ENV_FILE} (ignored by git).")


def chroma_client():
    """The local ChromaDB, with ChromaDB's telemetry switched off."""
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(
        path=str(CHROMA_DIR),
        settings=Settings(anonymized_telemetry=os.environ.get("ANONYMIZED_TELEMETRY", "False").lower() == "true"),
    )
