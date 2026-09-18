"""Tests for session recovery guard — blocks on session start if recovery items exist."""

from pathlib import Path


def test_session_recovery_guard_file_exists():
    """plugins/guards/session-recovery-guard.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    assert guard_file.exists(), f"Guard file not found at {guard_file}"


def test_guard_references_recovery_script():
    """plugins/guards/session-recovery-guard.ts contains reference to session_recovery.py."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    content = guard_file.read_text()
    
    assert "session_recovery.py" in content, "session_recovery.py reference not found in guard file"


def test_guard_checks_exit_code():
    """plugins/guards/session-recovery-guard.ts checks exit code."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    content = guard_file.read_text()
    
    # Check for exit code checking patterns
    has_exit_code_check = (
        "exitCode" in content or 
        "exit_code" in content or 
        ".code" in content or
        "code ===" in content or
        "code ===" in content
    )
    assert has_exit_code_check, "Exit code check not found in guard file"


def test_guard_throws_on_recovery_needed():
    """plugins/guards/session-recovery-guard.ts throws Error when recovery is needed."""
    repo_root = Path(__file__).resolve().parent.parent
    guard_file = repo_root / "plugins" / "guards" / "session-recovery-guard.ts"
    content = guard_file.read_text()
    
    assert "throw" in content, "throw statement not found in guard file"
    assert "Error" in content, "Error class not found in guard file"
    assert "recovery required" in content.lower(), "recovery required message not found in guard file"


def test_session_state_exists():
    """plugins/helpers/session-state.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    state_file = repo_root / "plugins" / "helpers" / "session-state.ts"
    assert state_file.exists(), f"Session state file not found at {state_file}"


def test_session_state_exports_class():
    """plugins/helpers/session-state.ts exports SessionState class."""
    repo_root = Path(__file__).resolve().parent.parent
    state_file = repo_root / "plugins" / "helpers" / "session-state.ts"
    content = state_file.read_text()
    
    assert "SessionState" in content, "SessionState class not found in session-state file"
    assert "export" in content, "export keyword not found in session-state file"


def test_session_state_has_recovery_methods():
    """plugins/helpers/session-state.ts has markRecoveryDone and isRecoveryDone methods."""
    repo_root = Path(__file__).resolve().parent.parent
    state_file = repo_root / "plugins" / "helpers" / "session-state.ts"
    content = state_file.read_text()
    
    assert "markRecoveryDone" in content, "markRecoveryDone method not found in session-state file"
    assert "isRecoveryDone" in content, "isRecoveryDone method not found in session-state file"


def test_plugin_imports_session_recovery_guard():
    """plugins/pipeline-enforcement.ts imports session-recovery-guard."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "session-recovery-guard" in content, "session-recovery-guard import not found in plugin file"


def test_plugin_imports_session_state():
    """plugins/pipeline-enforcement.ts imports SessionState."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "SessionState" in content, "SessionState import not found in plugin file"


def test_plugin_creates_session_state_instance():
    """plugins/pipeline-enforcement.ts creates SessionState instance."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "new SessionState" in content, "SessionState instantiation not found in plugin file"


def test_plugin_calls_session_recovery_guard():
    """plugins/pipeline-enforcement.ts calls sessionRecoveryGuard in tool.execute.before."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "sessionRecoveryGuard" in content, "sessionRecoveryGuard call not found in plugin file"
