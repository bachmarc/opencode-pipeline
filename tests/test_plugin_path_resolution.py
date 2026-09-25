"""Tests for plugin path resolution — session-recovery-guard uses framework-relative paths."""

import re
from pathlib import Path


def test_uses_import_meta_dirname():
    """session-recovery-guard.ts uses import.meta.dirname for path resolution."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"
    
    content = guard_file.read_text()
    assert "import.meta.dirname" in content, "import.meta.dirname not found in session-recovery-guard.ts"


def test_no_directory_scripts_reference():
    """session-recovery-guard.ts does not reference ${directory}/scripts/."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"
    
    content = guard_file.read_text()
    # Check for the old pattern: ${directory}/scripts/
    assert "${directory}/scripts/" not in content, "${directory}/scripts/ reference found in session-recovery-guard.ts"


def test_framework_not_installed_message():
    """session-recovery-guard.ts contains 'Framework not installed' error message."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"
    
    content = guard_file.read_text()
    assert "Framework not installed" in content, "Framework not installed message not found in session-recovery-guard.ts"
