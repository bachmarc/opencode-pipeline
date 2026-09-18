"""Tests for Documenter agent and /document command (Story 06-10).

Checks:
1. agent/documenter.md exists with required frontmatter (description, mode, temperature)
2. mode is exactly 'subagent'
3. command/document.md exists with agent: documenter
4. agent/qa-manager.md references documenter spawn after PASS
5. No concrete model names in agent/documenter.md
6. Documenter prompt clearly states boundaries (what it does NOT do)

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def parse_frontmatter(text: str, filename: str) -> dict[str, str]:
    """Parse a simple ``---`` delimited key-value frontmatter block.

    Raises AssertionError (with the filename) when the block is missing or
    malformed. Values must be single-line ``key: value`` pairs; the delimiter
    must be exactly ``---``.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise AssertionError(f"{filename}: frontmatter missing (no leading '---')")
    try:
        end = lines.index("---", 1)
    except ValueError:
        raise AssertionError(
            f"{filename}: frontmatter not terminated (no closing '---')"
        ) from None

    meta: dict[str, str] = {}
    for lineno, line in enumerate(lines[1:end], start=2):
        stripped = line.strip()
        if not stripped:  # blank lines inside the block are tolerated
            continue
        if ":" not in stripped:
            raise AssertionError(
                f"{filename}: frontmatter line {lineno} not 'key: value': {stripped!r}"
            )
        key, _, value = stripped.partition(":")
        key = key.strip()
        if not key:
            raise AssertionError(
                f"{filename}: frontmatter line {lineno} has empty key: {stripped!r}"
            )
        meta[key] = value.strip()
    return meta


def test_documenter_frontmatter() -> None:
    """agent/documenter.md has required keys (description, mode, temperature)."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "documenter.md")

    required_keys = ("description", "mode", "temperature")
    for key in required_keys:
        assert key in meta, (
            f"documenter.md: frontmatter missing required key {key!r} "
            f"(has: {sorted(meta)})"
        )


def test_documenter_mode_subagent() -> None:
    """agent/documenter.md mode is exactly 'subagent'."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "documenter.md")

    assert meta.get("mode") == "subagent", (
        f"documenter.md: mode must be 'subagent', got {meta.get('mode')!r}"
    )


def test_document_command_exists() -> None:
    """command/document.md exists with agent: documenter."""
    document_cmd_path = REPO_ROOT / "command" / "document.md"
    assert document_cmd_path.is_file(), f"missing {document_cmd_path.relative_to(REPO_ROOT)}"

    content = document_cmd_path.read_text(encoding="utf-8")
    meta = parse_frontmatter(content, "document.md")

    assert "agent" in meta, (
        f"document.md: frontmatter missing required key 'agent' "
        f"(has: {sorted(meta)})"
    )
    assert meta.get("agent") == "documenter", (
        f"document.md: agent must be 'documenter', got {meta.get('agent')!r}"
    )


def test_qa_manager_references_documenter() -> None:
    """agent/qa-manager.md contains 'documenter' (spawn instruction)."""
    qa_manager_path = REPO_ROOT / "agent" / "qa-manager.md"
    assert qa_manager_path.is_file(), f"missing {qa_manager_path.relative_to(REPO_ROOT)}"

    content = qa_manager_path.read_text(encoding="utf-8")
    assert "documenter" in content.lower(), (
        "qa-manager.md: must reference 'documenter' spawn instruction after PASS"
    )


def test_documenter_no_model_names() -> None:
    """No concrete model/provider names in agent/documenter.md."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")

    # Forbidden patterns: concrete model/provider names (case-insensitive)
    forbidden_patterns = (
        "glm-",
        "deepseek",
        "qwen",
        "haiku",
        "claude-",
        "ollama-docker",
        ":cloud",
        "anthropic/",
    )

    violations: list[str] = []
    for lineno, line in enumerate(content.splitlines(), start=1):
        lowered = line.lower()
        for pattern in forbidden_patterns:
            if pattern in lowered:
                violations.append(f"documenter.md:{lineno}: {line.strip()[:100]}")
                break

    assert not violations, (
        "model/provider names found in documenter.md:\n" + "\n".join(violations)
    )


def test_documenter_states_boundaries() -> None:
    """Documenter prompt clearly states boundaries (what it does NOT do)."""
    documenter_path = REPO_ROOT / "agent" / "documenter.md"
    assert documenter_path.is_file(), f"missing {documenter_path.relative_to(REPO_ROOT)}"

    content = documenter_path.read_text(encoding="utf-8")

    # Check for boundary markers in the prompt body (after frontmatter)
    lines = content.splitlines()
    try:
        end_frontmatter = lines.index("---", 1)
    except ValueError:
        raise AssertionError("documenter.md: frontmatter not terminated")

    prompt_body = "\n".join(lines[end_frontmatter + 1 :])

    # Look for explicit boundary statements (case-insensitive)
    boundary_keywords = (
        "does not",
        "does not make",
        "does not write",
        "does not judge",
        "does not invent",
        "boundary",
        "NOT do",
    )

    found_boundary = any(
        keyword.lower() in prompt_body.lower() for keyword in boundary_keywords
    )
    assert found_boundary, (
        "documenter.md: prompt must clearly state boundaries "
        "(what it does NOT do) — use 'does not', 'boundary', etc."
    )
