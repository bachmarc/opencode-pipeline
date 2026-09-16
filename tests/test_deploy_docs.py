"""Deployment docs presence checks (Story 01-04).

Docs story: the README must document the deploy procedure from design §1/§4.
Checks are marker-presence only (not exact prose) to stay deterministic.

External dependencies: none — reads the repo's own README.md.
"""

from pathlib import Path

import pytest

README_PATH = Path(__file__).resolve().parent.parent / "README.md"


@pytest.fixture(scope="module")
def readme_text() -> str:
    return README_PATH.read_text(encoding="utf-8")


def test_readme_deployment_section(readme_text: str) -> None:
    """README contains the Deployment section with all required markers."""
    # Section heading present
    assert "## Deployment" in readme_text, "missing '## Deployment' section heading"

    # Pull procedure targeting the live clone (~/.config/opencode)
    pull_marker = "git -C ~/.config/opencode pull origin main"
    assert pull_marker in readme_text, (
        "missing pull procedure (expected marker: "
        f"'{pull_marker}')"
    )

    # Restart requirement (config is loaded at startup, no hot-reload)
    assert "restart" in readme_text.lower(), "missing restart hint"

    # Gitignored local files mentioned (either marker suffices)
    assert ("cron.db" in readme_text) or ("opencode.jsonc" in readme_text), (
        "missing gitignored local files hint (cron.db / opencode.jsonc)"
    )

    # Rollback procedure
    assert "rollback" in readme_text.lower(), "missing rollback hint"