"""Tests for qa_compress.py --fast mode (story 22-01).

Tests for the get_changed_test_modules() function that maps changed files
to test modules by name convention:
  - scripts/foo.py         -> tests/test_foo.py
  - plugins/guards/foo.ts  -> tests/test_foo.py (dashes to underscores)
  - plugins/foo.ts         -> tests/test_foo.py

Tests mock subprocess.run for git diff output and verify the mapping logic.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def _restore_stdout():
    """Restore sys.stdout after each test to avoid issues with qa_compress.py modifying it."""
    original_stdout = sys.stdout
    yield
    sys.stdout = original_stdout


def test_fast_mode_maps_scripts_to_tests() -> None:
    """Mock git diff returning scripts/merge_if_passed.py -> tests/test_merge_if_passed.py."""
    # Import here to avoid issues if qa_compress.py doesn't exist yet
    from scripts.qa_compress import get_changed_test_modules
    
    git_output = "scripts/merge_if_passed.py\n"
    
    with patch("scripts.qa_compress.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=git_output,
            returncode=0,
        )
        
        result = get_changed_test_modules(REPO_ROOT)
        
        # Should contain the mapped test file (if it exists)
        # The function returns only existing files
        assert isinstance(result, list)
        # If test file exists, it should be in the result
        test_file = REPO_ROOT / "tests" / "test_merge_if_passed.py"
        if test_file.exists():
            assert str(test_file) in result or "tests/test_merge_if_passed.py" in result


def test_fast_mode_maps_plugin_guards() -> None:
    """Mock git diff returning plugins/guards/merge-guard.ts -> tests/test_merge_guard.py."""
    from scripts.qa_compress import get_changed_test_modules
    
    git_output = "plugins/guards/merge-guard.ts\n"
    
    with patch("scripts.qa_compress.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=git_output,
            returncode=0,
        )
        
        result = get_changed_test_modules(REPO_ROOT)
        
        assert isinstance(result, list)
        # If test file exists, it should be in the result
        test_file = REPO_ROOT / "tests" / "test_merge_guard.py"
        if test_file.exists():
            # Check if the test file is in the result (as string path)
            result_str = [str(r) for r in result]
            assert any("test_merge_guard.py" in r for r in result_str)


def test_fast_mode_fallback_on_no_match() -> None:
    """Mock git diff returning README.md -> empty list (no matching test module)."""
    from scripts.qa_compress import get_changed_test_modules
    
    git_output = "README.md\n"
    
    with patch("scripts.qa_compress.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=git_output,
            returncode=0,
        )
        
        result = get_changed_test_modules(REPO_ROOT)
        
        # README.md has no mapping, so result should be empty
        assert result == []


def test_fast_mode_dash_to_underscore() -> None:
    """Mock git diff returning plugins/guards/dev-start-guard.ts -> tests/test_dev_start_guard.py."""
    from scripts.qa_compress import get_changed_test_modules
    
    git_output = "plugins/guards/dev-start-guard.ts\n"
    
    with patch("scripts.qa_compress.subprocess.run") as mock_run:
        mock_run.return_value = MagicMock(
            stdout=git_output,
            returncode=0,
        )
        
        result = get_changed_test_modules(REPO_ROOT)
        
        assert isinstance(result, list)
        # If test file exists, it should be in the result with underscores
        test_file = REPO_ROOT / "tests" / "test_dev_start_guard.py"
        if test_file.exists():
            result_str = [str(r) for r in result]
            assert any("test_dev_start_guard.py" in r for r in result_str)
