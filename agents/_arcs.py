"""
The six emotional arc shapes, grounded in Reagan et al. (2016) / Vonnegut.
Source: vault/theory/reagan_arcs.md
Shared by Sean (critical diagnostic) and Richard (structural commitment at plot generation).
"""

from pathlib import Path
import config

_path = config.VAULT / "theory" / "reagan_arcs.md"
ARCS = _path.read_text() if _path.exists() else ""
