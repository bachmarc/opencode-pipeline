"""Test suite for story 06-12: Agent prompt updates for script integration.

Checks:
1. Agent prompts reference the correct scripts (worktree_setup, create_story, etc.)
2. No agent prompt instructs free-hand git worktree/branch/merge operations
3. Session recovery instruction is present
4. Intent tracking instruction is present
5. Template AGENTS.md updated with new conventions
6. No concrete model/provider names introduced
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_DIR = REPO_ROOT / "agent"
TEMPLATE_PATH = REPO_ROOT / "templates" / "AGENTS.md"


def test_architect_references_scripts() -> None:
    """architect.md contains references to required scripts."""
    architect_path = AGENT_DIR / "architect.md"
    assert architect_path.exists(), f"{architect_path} not found"
    
    content = architect_path.read_text(encoding="utf-8")
    required_scripts = [
        "worktree_setup",
        "create_story",
        "resolve_story",
        "merge_if_passed",
        "session_recovery",
        "intent",
    ]
    
    for script in required_scripts:
        assert script in content, (
            f"architect.md missing reference to {script}"
        )


def test_developer_references_scripts() -> None:
    """developer.md contains references to required scripts."""
    developer_path = AGENT_DIR / "developer.md"
    assert developer_path.exists(), f"{developer_path} not found"
    
    content = developer_path.read_text(encoding="utf-8")
    required_scripts = [
        "prepare_commit_metadata",
        "intent",
        "resolve_story",
    ]
    
    for script in required_scripts:
        assert script in content, (
            f"developer.md missing reference to {script}"
        )


def test_qa_manager_references_scripts() -> None:
    """qa-manager.md contains references to required scripts."""
    qa_manager_path = AGENT_DIR / "qa-manager.md"
    assert qa_manager_path.exists(), f"{qa_manager_path} not found"
    
    content = qa_manager_path.read_text(encoding="utf-8")
    required_scripts = [
        "qa_route",
        "pipeline_status",
    ]
    
    for script in required_scripts:
        assert script in content, (
            f"qa-manager.md missing reference to {script}"
        )


def test_no_freehand_git_worktree() -> None:
    """No agent prompt contains 'git worktree add' as a direct instruction."""
    agent_files = sorted(AGENT_DIR.glob("*.md"))
    assert agent_files, "no agent/*.md files found"
    
    violations: list[str] = []
    for path in agent_files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        content = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(content.splitlines(), start=1):
            if "git worktree add" in line:
                violations.append(f"{rel}:{lineno}: {line.strip()[:100]}")
    
    assert not violations, (
        "agent prompts contain free-hand 'git worktree add' instructions:\n"
        + "\n".join(violations)
    )


def test_template_has_recovery() -> None:
    """templates/AGENTS.md references session_recovery."""
    assert TEMPLATE_PATH.exists(), f"{TEMPLATE_PATH} not found"
    
    content = TEMPLATE_PATH.read_text(encoding="utf-8")
    assert "session_recovery" in content or "session recovery" in content.lower(), (
        "templates/AGENTS.md missing reference to session_recovery"
    )


def test_no_model_names() -> None:
    """Existing model-name check still passes (no concrete model/provider names)."""
    PORTABLE_DIRS = ("agent", "command", "skills", "templates", "scripts")
    PORTABLE_SUFFIXES = (".md", ".sh", ".py", ".txt", ".json")
    
    FORBIDDEN_PATTERNS = (
        "glm-",
        "deepseek",
        "qwen",
        "haiku",
        "claude-",
        "ollama-docker",
        ":cloud",
        "anthropic/",
    )
    
    ALLOWLIST_SUBSTRINGS = ("CLAUDE.md",)
    
    def _is_allowed(line: str) -> bool:
        return any(marker in line for marker in ALLOWLIST_SUBSTRINGS)
    
    violations: list[str] = []
    checked = 0
    
    for dirname in PORTABLE_DIRS:
        base = REPO_ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in PORTABLE_SUFFIXES:
                rel = path.relative_to(REPO_ROOT).as_posix()
                checked += 1
                for lineno, line in enumerate(
                    path.read_text(encoding="utf-8").splitlines(), start=1
                ):
                    if _is_allowed(line):
                        continue
                    lowered = line.lower()
                    for pattern in FORBIDDEN_PATTERNS:
                        if pattern in lowered:
                            violations.append(f"{rel}:{lineno}: {line.strip()[:100]}")
                            break
    
    assert checked > 0, "no portable files found to scan"
    assert not violations, (
        "model/provider names found in portable files:\n" + "\n".join(violations)
    )
