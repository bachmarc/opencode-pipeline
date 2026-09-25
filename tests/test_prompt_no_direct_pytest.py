"""
Invariant: agent/developer.md and agent/qa-manager.md must NOT contain direct pytest invocations.

Story 17-04 (qa_compress.sh as sole test entry point): qa_compress.sh is the framework's
deterministic test runner that reads qa_config.json and runs all configured checkers.
Direct pytest calls silently skip non-pytest checkers. Prompts must describe qa_compress.sh
as the sole test runner, never direct pytest invocations like `pytest tests/` or
`python -m pytest`.

pytest may still appear as a checker name in qa_config.json examples/context — this test
only checks for direct shell command invocations outside code blocks.
"""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read_markdown_lines(path: Path) -> list[str]:
    """Read markdown file and return non-code-block lines."""
    content = path.read_text(encoding="utf-8")
    lines = content.splitlines()
    
    # Simple code-block detection: skip lines between ``` markers
    in_code_block = False
    result = []
    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if not in_code_block:
            result.append(line)
    return result


def _find_direct_pytest_invocations(path: Path) -> list[tuple[int, str]]:
    """
    Find direct pytest invocations (pytest tests/ or python -m pytest) in non-code-block lines.
    Returns list of (line_number, line_content) tuples.
    """
    lines = _read_markdown_lines(path)
    violations = []
    
    # Pattern: pytest tests or python -m pytest (at start of line or after whitespace)
    pattern = re.compile(r"^\s*(python\s+-m\s+pytest|pytest\s+tests)")
    
    for lineno, line in enumerate(lines, start=1):
        if pattern.search(line):
            violations.append((lineno, line.strip()))
    
    return violations


def test_developer_md_no_direct_pytest() -> None:
    """agent/developer.md must not contain direct pytest invocations."""
    dev_path = REPO_ROOT / "agent" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    violations = _find_direct_pytest_invocations(dev_path)
    assert not violations, (
        f"agent/developer.md contains direct pytest invocations:\n"
        + "\n".join(f"  line {lineno}: {line}" for lineno, line in violations)
    )


def test_qa_manager_md_no_direct_pytest() -> None:
    """agent/qa-manager.md must not contain direct pytest invocations."""
    qa_path = REPO_ROOT / "agent" / "qa-manager.md"
    assert qa_path.exists(), f"{qa_path} not found"
    
    violations = _find_direct_pytest_invocations(qa_path)
    assert not violations, (
        f"agent/qa-manager.md contains direct pytest invocations:\n"
        + "\n".join(f"  line {lineno}: {line}" for lineno, line in violations)
    )


def test_qa_compress_mentioned_in_developer() -> None:
    """agent/developer.md must mention qa_compress.sh as the test runner."""
    dev_path = REPO_ROOT / "agent" / "developer.md"
    assert dev_path.exists(), f"{dev_path} not found"
    
    content = dev_path.read_text(encoding="utf-8")
    assert "qa_compress.sh" in content, (
        "agent/developer.md must mention 'qa_compress.sh' as the test runner"
    )


def test_qa_compress_mentioned_in_qa_manager() -> None:
    """agent/qa-manager.md must mention qa_compress.sh as the test runner."""
    qa_path = REPO_ROOT / "agent" / "qa-manager.md"
    assert qa_path.exists(), f"{qa_path} not found"
    
    content = qa_path.read_text(encoding="utf-8")
    assert "qa_compress.sh" in content, (
        "agent/qa-manager.md must mention 'qa_compress.sh' as the test runner"
    )
