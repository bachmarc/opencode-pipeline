"""Tests for architect code guard — blocks architect from editing code files."""

from pathlib import Path


def test_architect_code_guard_file_exists():
    """plugins/guards/architect-code-guard.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "architect-code-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_guard_has_code_patterns():
    """architect-code-guard.ts contains code file patterns (.py, .ts, .js, .sh, src/, tests/)."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "architect-code-guard.ts"
    content = guard_file.read_text()
    
    # Check for code patterns
    assert ".py" in content, "Code pattern .py not found"
    assert ".ts" in content, "Code pattern .ts not found"
    assert ".js" in content, "Code pattern .js not found"
    assert ".sh" in content, "Code pattern .sh not found"
    assert "src/" in content, "Path pattern src/ not found"
    assert "tests/" in content, "Path pattern tests/ not found"


def test_guard_checks_agent():
    """architect-code-guard.ts checks agent identity (architect or build)."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "architect-code-guard.ts"
    content = guard_file.read_text()
    
    # Check for agent checks
    assert "architect" in content.lower(), "Agent check for 'architect' not found"
    assert "build" in content.lower(), "Agent check for 'build' not found"


def test_guard_blocks_architect_code():
    """architect-code-guard.ts returns block for architect + code file."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "architect-code-guard.ts"
    content = guard_file.read_text()
    
    # Check for block logic
    assert "block" in content.lower(), "Block action not found"
    assert "Architect code edit blocked" in content, "Block message not found"


def test_housekeeping_log_exists():
    """plugins/helpers/housekeeping-log.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    log_file = repo_root / "plugins" / "helpers" / "housekeeping-log.ts"
    assert log_file.exists(), f"Housekeeping log file not found at {log_file}"


def test_plugin_imports_architect_guard():
    """plugins/pipeline-enforcement.ts imports architect-code-guard."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "architect-code-guard" in content, "architect-code-guard import not found in pipeline-enforcement.ts"
