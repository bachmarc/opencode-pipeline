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
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# --- Check 1: agent frontmatter -------------------------------------------------

AGENT_DIR = REPO_ROOT / "agents"
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

PORTABLE_DIRS = ("agents", "command", "skills", "templates", "scripts")
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


# --- Check 4: qa_compress.py is syntactically valid --------------------------------

QA_COMPRESS_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


def test_qa_compress_script() -> None:
    """scripts/qa_compress.py exists and passes `python -m py_compile` (syntax check)."""
    rel = QA_COMPRESS_SCRIPT.relative_to(REPO_ROOT).as_posix()
    assert QA_COMPRESS_SCRIPT.is_file(), f"missing {rel}"

    result = subprocess.run(
        [sys.executable, "-m", "py_compile", rel],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, (
        f"python -m py_compile {rel} failed (rc={result.returncode}):\n"
        f"{result.stderr.strip()}"
    )


# --- Check 5: developer prompt has code documentation rule ----------------------

def test_developer_prompt_has_code_doc_rule() -> None:
    """agent/developer.md contains code documentation rule in Rules section."""
    developer_path = AGENT_DIR / "developer.md"
    assert developer_path.is_file(), f"missing {developer_path.relative_to(REPO_ROOT)}"
    
    content = developer_path.read_text(encoding="utf-8")
    
    # Check for Rules section
    assert "## Rules" in content, "developer.md missing '## Rules' section"
    
    # Extract the Rules section (from "## Rules" to the next "##" or end of file)
    start_idx = content.find("## Rules")
    next_section_idx = content.find("\n##", start_idx + 1)
    if next_section_idx == -1:
        rules_section = content[start_idx:]
    else:
        rules_section = content[start_idx:next_section_idx]
    
    # Check for both "docstring" and "source of truth" in the rules section
    has_docstring = "docstring" in rules_section.lower()
    has_source_of_truth = "source of truth" in rules_section.lower()
    
    assert has_docstring, (
        "developer.md Rules section missing 'docstring' reference"
    )
    assert has_source_of_truth, (
        "developer.md Rules section missing 'source of truth' reference"
    )


# --- Check 6: clarification markers in story template and workflow ----------------

def test_story_template_has_clarification_guidance() -> None:
    """docs/features/_story_template.md contains [NEEDS CLARIFICATION guidance."""
    template_path = REPO_ROOT / "docs" / "features" / "_story_template.md"
    assert template_path.is_file(), f"missing {template_path.relative_to(REPO_ROOT)}"
    
    content = template_path.read_text(encoding="utf-8")
    assert "[NEEDS CLARIFICATION" in content, (
        "_story_template.md must contain '[NEEDS CLARIFICATION' guidance for architects"
    )


def test_architect_prompt_has_clarification_rule() -> None:
    """agent/architect.md contains NEEDS CLARIFICATION marker convention."""
    architect_path = AGENT_DIR / "architect.md"
    assert architect_path.is_file(), f"missing {architect_path.relative_to(REPO_ROOT)}"
    
    content = architect_path.read_text(encoding="utf-8")
    assert "NEEDS CLARIFICATION" in content, (
        "architect.md must contain 'NEEDS CLARIFICATION' marker convention in story-decomposition rules"
    )


def test_qa_prompt_has_clarification_check() -> None:
    """agent/qa-manager.md checklist includes NEEDS CLARIFICATION check."""
    qa_path = AGENT_DIR / "qa-manager.md"
    assert qa_path.is_file(), f"missing {qa_path.relative_to(REPO_ROOT)}"
    
    content = qa_path.read_text(encoding="utf-8")
    assert "NEEDS CLARIFICATION" in content, (
        "qa-manager.md must contain 'NEEDS CLARIFICATION' check in Requirements checklist"
    )


# --- Check 7: feature.md stories match actual files --------------------------------

def _extract_story_ids_from_feature_md(feature_md_content: str) -> set[str]:
    """Extract story IDs from feature.md '## Stories' section.
    
    Returns a set of story ID prefixes (e.g. '01-01', '02-03').
    Expects lines of the form: '- XX-YY-slug (status)' or '- XX-YY-slug'.
    """
    story_ids = set()
    lines = feature_md_content.splitlines()
    
    # Find the Stories section
    in_stories_section = False
    for line in lines:
        if line.strip() == "## Stories":
            in_stories_section = True
            continue
        
        # Exit stories section when we hit another section
        if in_stories_section and line.startswith("##"):
            break
        
        if in_stories_section:
            # Look for lines like "- 01-01-slug (status)" or "- XX-YY-slug"
            stripped = line.strip()
            if stripped.startswith("- "):
                # Extract the part after "- "
                rest = stripped[2:].strip()
                # Find the story ID (XX-YY part)
                parts = rest.split("-", 2)  # Split on first two hyphens
                if len(parts) >= 2:
                    # parts[0] = XX, parts[1] = YY, parts[2] = rest (slug and status)
                    story_id = f"{parts[0]}-{parts[1]}"
                    # Verify it looks like a story ID (two digit groups)
                    if parts[0].isdigit() and parts[1].isdigit():
                        story_ids.add(story_id)
    
    return story_ids


def _extract_story_ids_from_filenames(stories_dir: Path) -> set[str]:
    """Extract story IDs from .md filenames in a stories/ directory.
    
    Returns a set of story ID prefixes (e.g. '01-01', '02-03').
    Expects filenames like 'XX-YY-slug.md'.
    """
    story_ids = set()
    if not stories_dir.is_dir():
        return story_ids
    
    for md_file in stories_dir.glob("*.md"):
        filename = md_file.name
        # Extract XX-YY from 'XX-YY-slug.md'
        parts = filename.rstrip(".md").split("-", 2)  # Split on first two hyphens
        if len(parts) >= 2 and parts[0].isdigit() and parts[1].isdigit():
            story_id = f"{parts[0]}-{parts[1]}"
            story_ids.add(story_id)
    
    return story_ids


def test_feature_md_stories_match_files() -> None:
    """Each feature.md '## Stories' section lists exactly the .md files in stories/.
    
    Fails with a clear diff if there are:
    - Stories listed in feature.md but missing as files (extras in feature.md)
    - Stories existing as files but not listed in feature.md (missing in feature.md)
    """
    features_dir = REPO_ROOT / "docs" / "features"
    assert features_dir.is_dir(), f"missing {features_dir.relative_to(REPO_ROOT)}"
    
    mismatches = []
    
    # Iterate over all feature directories
    for feature_dir in sorted(features_dir.iterdir()):
        if not feature_dir.is_dir() or feature_dir.name.startswith("_"):
            continue
        
        feature_md_path = feature_dir / "feature.md"
        stories_dir = feature_dir / "stories"
        
        if not feature_md_path.is_file():
            continue
        
        # Read feature.md and extract story IDs from the Stories section
        feature_md_content = feature_md_path.read_text(encoding="utf-8")
        listed_ids = _extract_story_ids_from_feature_md(feature_md_content)
        
        # Extract story IDs from actual .md files in stories/ directory
        file_ids = _extract_story_ids_from_filenames(stories_dir)
        
        # Compare
        extras_in_md = listed_ids - file_ids  # In feature.md but not as files
        missing_in_md = file_ids - listed_ids  # In files but not in feature.md
        
        if extras_in_md or missing_in_md:
            rel = feature_dir.relative_to(REPO_ROOT).as_posix()
            msg_parts = [f"{rel}:"]
            if extras_in_md:
                msg_parts.append(
                    f"  Listed in feature.md but missing as files: {sorted(extras_in_md)}"
                )
            if missing_in_md:
                msg_parts.append(
                    f"  Exist as files but not listed in feature.md: {sorted(missing_in_md)}"
                )
            mismatches.append("\n".join(msg_parts))
    
    assert not mismatches, (
        "Feature.md stories sections do not match actual .md files:\n\n"
        + "\n\n".join(mismatches)
    )
