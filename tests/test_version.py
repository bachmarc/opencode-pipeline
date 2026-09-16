"""Version anchor check (Story 01-05).

The repo carries an ``APP_VERSION.py`` anchor at the repo root defining the
pipeline version (convention from AGENTS.md, design §6). This test ensures the
anchor exists, is importable, and holds the current version in semver format.

External dependencies: none — imports the repo's own version anchor.
"""

import re
import sys
from pathlib import Path

# tests/ is not a package — make the repo root importable so APP_VERSION.py
# (repo root) can be imported directly.
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from APP_VERSION import APP_VERSION  # noqa: E402  (repo-root import)

SEMVER_PATTERN = r"^\d+\.\d+\.\d+$"


def test_app_version() -> None:
    """APP_VERSION is importable, matches semver X.Y.Z and holds "0.1.0"."""
    assert re.match(SEMVER_PATTERN, APP_VERSION), (
        f"APP_VERSION {APP_VERSION!r} does not match semver pattern "
        f"'{SEMVER_PATTERN}'"
    )
    assert APP_VERSION == "0.1.0", (
        f"APP_VERSION is {APP_VERSION!r}, expected '0.1.0'"
    )