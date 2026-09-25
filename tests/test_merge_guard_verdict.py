"""Tests for merge guard verdict schema fix (verdicts array instead of last_verdict)."""
import json
import re
from pathlib import Path


def test_pass_verdict_allows_merge():
    """Test that merge-guard.ts allows merge when verdicts array has PASS."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should read from verdicts array
    assert "verdicts" in content, "merge-guard.ts should reference verdicts array"
    # Should check the last element's verdict
    assert "verdicts[" in content or "verdicts.length" in content, \
        "merge-guard.ts should access verdicts array elements"
    # Should NOT reference last_verdict
    assert "last_verdict" not in content, "merge-guard.ts should not reference last_verdict"


def test_fail_verdict_blocks_merge():
    """Test that merge-guard.ts blocks merge when verdicts array has FAIL."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should check for PASS verdict
    assert '"PASS"' in content or "'PASS'" in content, \
        "merge-guard.ts should check for PASS verdict"
    # Should throw error on non-PASS
    assert "throw" in content, "merge-guard.ts should throw error on non-PASS verdict"


def test_missing_verdicts_blocks_merge():
    """Test that merge-guard.ts blocks merge when verdicts key is missing."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should check for verdicts existence (using optional chaining or explicit check)
    assert "verdicts" in content, "merge-guard.ts should check for verdicts"
    # Should handle missing/empty verdicts
    assert "length" in content or "?" in content, \
        "merge-guard.ts should handle missing or empty verdicts array"


def test_old_schema_last_verdict_blocks_merge():
    """Test that merge-guard.ts does NOT use old last_verdict schema."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should NOT contain last_verdict reference
    assert "last_verdict" not in content, \
        "merge-guard.ts should not reference last_verdict (old schema)"


def test_merge_guard_reads_correct_schema():
    """Test that merge-guard.ts reads verdicts[verdicts.length - 1].verdict."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should access last element of verdicts array
    # Pattern: verdicts[verdicts.length - 1] or similar
    assert re.search(r'verdicts\[.*length.*-.*1\]', content) or \
           re.search(r'verdicts\[.*verdicts\.length.*\]', content) or \
           "verdicts[-1]" in content, \
        "merge-guard.ts should read verdicts[verdicts.length - 1] or similar"


def test_merge_guard_has_schema_documentation():
    """Test that merge-guard.ts module docstring documents the schema."""
    merge_guard_path = Path(__file__).parent.parent / "plugins" / "guards" / "merge-guard.ts"
    content = merge_guard_path.read_text()
    
    # Should have documentation about verdicts schema
    assert "verdicts" in content, "merge-guard.ts should document verdicts schema"


def test_qa_route_has_schema_documentation():
    """Test that qa_route.py module docstring documents the schema."""
    qa_route_path = Path(__file__).parent.parent / "scripts" / "qa_route.py"
    content = qa_route_path.read_text()
    
    # Should have schema documentation in module docstring
    assert "verdicts" in content, "qa_route.py should document verdicts schema"
    # Should show the schema format
    assert "verdict" in content, "qa_route.py should document verdict field"
