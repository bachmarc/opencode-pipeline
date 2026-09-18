"""Tests for Documenter Guard plugin."""

import os
from pathlib import Path


def test_documenter_guard_file_exists():
    """Test that plugins/guards/documenter-guard.ts exists."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "documenter-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_guard_checks_reconcile_pattern():
    """Test that documenter-guard.ts contains 'docs: reconcile' pattern."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "documenter-guard.ts"
    content = guard_file.read_text()
    assert "docs: reconcile" in content, "Guard does not check for 'docs: reconcile' pattern"


def test_guard_uses_git_log():
    """Test that documenter-guard.ts uses git log command."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "documenter-guard.ts"
    content = guard_file.read_text()
    assert "git log" in content, "Guard does not use 'git log' command"


def test_guard_throws_on_missing_documenter():
    """Test that documenter-guard.ts throws error when documenter commit not found."""
    guard_file = Path(__file__).parent.parent / "plugins" / "guards" / "documenter-guard.ts"
    content = guard_file.read_text()
    assert "throw" in content, "Guard does not throw on missing documenter"
    assert "Error" in content, "Guard does not throw Error"
    assert "Documenter not run" in content, "Guard error message does not mention 'Documenter not run'"


def test_plugin_imports_documenter_guard():
    """Test that pipeline-enforcement.ts imports documenter-guard."""
    plugin_file = Path(__file__).parent.parent / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    assert "documenter-guard" in content, "Plugin does not import documenter-guard"
