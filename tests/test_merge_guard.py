"""Tests for merge guard plugin."""
import os
import json
from pathlib import Path


def test_merge_guard_file_exists():
    """Test that plugins/guards/merge-guard.ts exists."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    assert merge_guard_path.exists(), f"merge-guard.ts not found at {merge_guard_path}"


def test_merge_guard_reads_qa_status():
    """Test that merge-guard.ts contains qa-state directory reference."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    assert "qa-state" in content, "merge-guard.ts should reference qa-state directory"


def test_merge_guard_throws_on_no_pass():
    """Test that merge-guard.ts throws error when no QA-PASS found."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    assert "throw" in content, "merge-guard.ts should contain throw statement"
    assert "Error" in content, "merge-guard.ts should throw Error"
    assert "Merge blocked" in content, "merge-guard.ts should contain 'Merge blocked' message"


def test_plugin_imports_merge_guard():
    """Test that pipeline-enforcement.ts imports merge-guard."""
    plugin_path = Path(__file__).parent.parent / "plugins" / "pipeline-enforcement.ts"
    content = plugin_path.read_text()
    assert "merge-guard" in content, "pipeline-enforcement.ts should import merge-guard"
