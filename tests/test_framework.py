"""Framework self-checks — the repo validates its own portable invariants.

Checks (design.md §3):
1. agent/*.md frontmatter: parseable block, required keys, no ``model:`` key.
2. No concrete model/provider names in portable files (role abstraction).
3. templates/AGENTS.md exists with constant section markers + placeholders.
4. scripts/qa_compress.sh passes ``bash -n``.

Stdlib only — no external systems, deterministic (repo files are the fixture).
"""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Check 1: agent frontmatter -------------------------------------------------

AGENT_DIR = REPO_ROOT / "agent"
FRONTMATTER_REQUIRED_KEYS = ("description", "mode")
FRONTMATTER_FORBIDDEN_KEYS = ("model",)


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


def test_agent_frontmatter() -> None:
    """Every agent/*.md has parseable frontmatter with required and no forbidden keys."""
    agent_files = sorted(AGENT_DIR.glob("*.md"))
    assert agent_files, "no agent/*.md files found"

    for path in agent_files:
        filename = path.name
        meta = parse_frontmatter(path.read_text(encoding="utf-8"), filename)

        for key in FRONTMATTER_REQUIRED_KEYS:
            assert key in meta, (
                f"{filename}: frontmatter missing required key {key!r} "
                f"(has: {sorted(meta)})"
            )
        for key in FRONTMATTER_FORBIDDEN_KEYS:
            assert key not in meta, (
                f"{filename}: frontmatter must not contain {key!r} — models are "
                f"configured only in the local opencode.jsonc"
            )


# --- Check 2: no model names in portable files -----------------------------------

PORTABLE_DIRS = ("agent", "command", "skills", "templates", "scripts")
PORTABLE_SUFFIXES = (".md", ".sh", ".py", ".txt", ".json")

# Case-insensitive forbidden patterns: concrete model/provider names.
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

# Allowlist: lines containing a legit file reference to CLAUDE.md — the substring
# "claude" inside the filename would otherwise trip the "claude-" pattern.
ALLOWLIST_SUBSTRINGS = ("CLAUDE.md",)


def _iter_portable_files() -> list[Path]:
    files: list[Path] = []
    for dirname in PORTABLE_DIRS:
        base = REPO_ROOT / dirname
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and path.suffix in PORTABLE_SUFFIXES:
                files.append(path)
    return files


def _is_allowed(line: str) -> bool:
    return any(marker in line for marker in ALLOWLIST_SUBSTRINGS)


def test_no_model_names_in_portable_files() -> None:
    """Portable files contain no concrete model/provider names (case-insensitive)."""
    violations: list[str] = []
    checked = 0

    for path in _iter_portable_files():
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


# --- Check 3: template exists and stays constant ----------------------------------

TEMPLATE_PATH = REPO_ROOT / "templates" / "AGENTS.md"
# (required marker, optional alternative) pairs — either variant satisfies the check.
TEMPLATE_REQUIRED_SECTIONS = (
    ("## Workflow", None),
    ("## Git", None),
    ("## Sprachen", "## Languages"),
    ("## Verbote", "## Prohibitions"),
)


def test_template_exists_and_const() -> None:
    """templates/AGENTS.md exists, keeps constant section markers and placeholders."""
    assert TEMPLATE_PATH.is_file(), f"missing {TEMPLATE_PATH.relative_to(REPO_ROOT)}"

    content = TEMPLATE_PATH.read_text(encoding="utf-8")

    for marker, alt in TEMPLATE_REQUIRED_SECTIONS:
        alternatives = (marker,) if alt is None else (marker, alt)
        assert any(m in content for m in alternatives), (
            f"templates/AGENTS.md: constant section marker {marker!r} "
            f"{'(or ' + alt + ') ' if alt else ''}missing"
        )

    # At least one `<` ... `>` placeholder pattern (e.g. <Projektname>).
    start = content.find("<")
    assert start != -1, "templates/AGENTS.md: no '<' placeholder found"
    end = content.find(">", start)
    assert end != -1, "templates/AGENTS.md: no '>' closing a placeholder"
    placeholder = content[start : end + 1]
    assert "..." in placeholder or placeholder[1:-1].strip(), (
        f"templates/AGENTS.md: placeholder {placeholder!r} is empty"
    )


# --- Check 4: qa_compress.sh is syntactically valid --------------------------------

QA_COMPRESS_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.sh"


def test_qa_compress_script() -> None:
    """scripts/qa_compress.sh exists and passes `bash -n` (syntax check)."""
    rel = QA_COMPRESS_SCRIPT.relative_to(REPO_ROOT).as_posix()
    assert QA_COMPRESS_SCRIPT.is_file(), f"missing {rel}"

    result = subprocess.run(
        ["bash", "-n", rel],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"bash -n {rel} failed (rc={result.returncode}):\n"
        f"{result.stderr.strip()}"
    )