#!/usr/bin/env python3
"""Prepare commit metadata from staged changes.

Analyzes git diff --cached to extract:
- Changed file names
- Changed export symbols (language-aware: Python AST, Ruby/JS/Java regex,
  other: file stem)
- Dependent files (per-language grep for imports/requires of changed modules)
- Test result (the project's configured test runner from qa_config.json)

Outputs formatted metadata string:
  symbols: ... | breaks: none|breaking | affects: ... | tests: ...

Exit code: 0 always (informational)
"""

from __future__ import annotations

import ast
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Test-runner checkers mapped to their standard quiet invocation
# (source: checker plugins under scripts/qa_checkers/). First matching
# checker in a project's declared list wins. Syntax checkers (json, yaml,
# html) are deliberately absent — they never provide a `tests:` result.
RUNNER_COMMANDS: dict[str, list[str]] = {
    "rspec": ["rspec"],
    "jest": ["jest"],
    "gradle": ["gradle", "test"],
    "maven": ["mvn", "test"],
    "pytest": ["python", "-m", "pytest", "--tb=no", "-q"],
}

# One grep pattern per language family to find files that depend on a
# changed module ({module} is the regex-escaped module name).
DEPENDENT_PATTERNS: dict[str, str] = {
    "py": r"(from|import)\s+{module}(\s|$|\.)",
    "rb": r"require.*{module}",
    "js": r"(import|require).*{module}",
    "java": r"import.*{module}",
}


def get_repo_root() -> Path:
    """Find repo root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def get_staged_files() -> list[str]:
    """Get list of staged files from git diff --cached."""
    result = subprocess.run(
        ["git", "diff", "--cached", "--name-only"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return []

    return [f for f in result.stdout.strip().split("\n") if f]


def load_qa_config(repo_root: Path) -> list[str]:
    """Read the checker list from qa_config.json in the repo root.

    Contract (same default logic as the QA gate, story 12-01):
    - No qa_config.json -> default ["pytest"] (backward compatible).
    - Malformed/unreadable config -> reported to stderr, treated as missing
      (loud default, no crash).
    - Valid config -> the declared checker list (may be empty = opt-out).
    """
    config_file = repo_root / "qa_config.json"
    if not config_file.is_file():
        return ["pytest"]
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, ValueError) as exc:
        print(
            f"qa_config.json: invalid, using default ['pytest']: {exc}",
            file=sys.stderr,
        )
        return ["pytest"]
    checkers = data.get("checkers") if isinstance(data, dict) else None
    if not isinstance(checkers, list) or not all(
        isinstance(checker, str) for checker in checkers
    ):
        print(
            'qa_config.json: "checkers" must be a list of strings, '
            "using default ['pytest']",
            file=sys.stderr,
        )
        return ["pytest"]
    return list(checkers)


def get_test_command(config_checkers: list[str]) -> tuple[str, list[str]] | None:
    """Map the first matching runner checker to its test invocation.

    Precedence: the first entry of ``config_checkers`` that is a known
    test-runner checker wins (rspec, jest, gradle, maven, pytest). Syntax
    checkers (json, yaml, html) and unknown names never match. Only syntax
    checkers (or an empty list) configured -> ``None``.
    """
    for checker in config_checkers:
        command = RUNNER_COMMANDS.get(checker)
        if command is not None:
            return (checker, list(command))
    return None


def extract_python_symbols(file_path: Path) -> list[str]:
    """Extract top-level function and class names from Python file."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
    except Exception:  # noqa: BLE001
        return []

    # Filter to only top-level (simple heuristic: no indentation in source)
    try:
        top_level = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                top_level.append(node.name)
        return top_level
    except Exception:  # noqa: BLE001
        return []


def extract_ruby_symbols(file_path: Path) -> list[str]:
    """Extract def/class/module names from a Ruby file (regex)."""
    try:
        content = file_path.read_text()
    except Exception:  # noqa: BLE001
        return []
    symbols: list[str] = []
    for match in re.finditer(
        r"^[ \t]*(?:def|class|module)\s+([A-Za-z_][A-Za-z0-9_!?]*)",
        content,
        re.MULTILINE,
    ):
        symbols.append(match.group(1))
    return symbols


def extract_js_symbols(file_path: Path) -> list[str]:
    """Extract function/class/const names from a JS/TS file (regex)."""
    try:
        content = file_path.read_text()
    except Exception:  # noqa: BLE001
        return []
    symbols: list[str] = []
    for match in re.finditer(
        r"\bfunction\s+([A-Za-z_$][\w$]*)"
        r"|\bclass\s+([A-Za-z_$][\w$]*)"
        r"|\bconst\s+([A-Za-z_$][\w$]*)\s*=",
        content,
        re.MULTILINE,
    ):
        name = match.group(1) or match.group(2) or match.group(3)
        if name:
            symbols.append(name)
    return symbols


def extract_java_symbols(file_path: Path) -> list[str]:
    """Extract class/interface names from a Java file (regex)."""
    try:
        content = file_path.read_text()
    except Exception:  # noqa: BLE001
        return []
    symbols: list[str] = []
    for match in re.finditer(
        r"\b(?:class|interface)\s+([A-Za-z_$][\w$]*)",
        content,
        re.MULTILINE,
    ):
        symbols.append(match.group(1))
    return symbols


def extract_symbols(file_path: Path) -> list[str]:
    """Extract changed symbols from a file (dispatch on suffix)."""
    suffix = file_path.suffix
    if suffix == ".py":
        return extract_python_symbols(file_path)
    if suffix == ".rb":
        return extract_ruby_symbols(file_path)
    if suffix in (".js", ".ts", ".jsx", ".tsx"):
        return extract_js_symbols(file_path)
    if suffix == ".java":
        return extract_java_symbols(file_path)

    # For other files, use filename as symbol
    return [file_path.stem]


def _language_family(suffix: str) -> str | None:
    """Map a file suffix to its language family (for dependent search)."""
    if suffix == ".py":
        return "py"
    if suffix == ".rb":
        return "rb"
    if suffix in (".js", ".ts", ".jsx", ".tsx"):
        return "js"
    if suffix == ".java":
        return "java"
    return None


def find_dependents(changed_files: list[str], repo_root: Path) -> list[str]:
    """Find files that import/require changed modules (per language)."""
    dependents: set[str] = set()

    # Module names per language family, derived from staged files of the
    # respective suffix (dotted path + bare stem, analogous to old .py logic).
    family_modules: dict[str, set[str]] = {}
    for file_path in changed_files:
        family = _language_family(Path(file_path).suffix)
        if family is None:
            continue
        modules = family_modules.setdefault(family, set())
        modules.add(Path(file_path).stem)
        modules.add(Path(file_path).as_posix().rsplit(".", 1)[0].replace("/", "."))

    # Search for imports/requires of these modules (one pattern per family)
    for family, modules in family_modules.items():
        for module in modules:
            escaped_module = re.escape(module)
            pattern = DEPENDENT_PATTERNS[family].format(module=escaped_module)
            result = subprocess.run(
                ["git", "grep", "-l", "-E", pattern],
                cwd=str(repo_root),
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split("\n"):
                    if line and line not in changed_files:
                        dependents.add(line)

    return sorted(dependents)


def run_test(command: list[str] | None) -> str:
    """Run the configured test command and return its result summary.

    Last non-empty output line (stdout first, fall back to stderr).
    ``command is None`` -> no runner configured (syntax checkers only).
    """
    if command is None:
        return "n/a (syntax checkers only)"
    
    # On Windows, subprocess.run() with a list doesn't find .cmd files on PATH.
    # Use shutil.which() to resolve the command first.
    exe = shutil.which(command[0])
    if exe is None:
        # Runner binary not available — informational only, never crash.
        return "unknown"
    
    # Replace the command name with the full path
    full_command = [exe] + command[1:]
    
    try:
        result = subprocess.run(
            full_command,
            capture_output=True,
            text=True,
            encoding="utf-8",
            check=False,
        )
    except OSError:
        # Runner binary not available — informational only, never crash.
        return "unknown"

    for stream_output in (result.stdout, result.stderr):
        lines = [line.strip() for line in stream_output.split("\n") if line.strip()]
        if lines:
            return lines[-1]

    return "unknown"


def format_metadata(
    symbols: list[str],
    breaks: str,
    affects: list[str],
    tests: str,
) -> str:
    """Format metadata as pipe-separated string."""
    symbols_str = ", ".join(symbols) if symbols else "none"
    affects_str = ", ".join(affects) if affects else "none"

    return f"symbols: {symbols_str} | breaks: {breaks} | affects: {affects_str} | tests: {tests}"


def main() -> int:
    """Main entry point."""
    repo_root = get_repo_root()

    # Get staged files
    staged_files = get_staged_files()

    # Extract language-aware symbols from staged files
    all_symbols = []
    for file_path_str in staged_files:
        file_path = repo_root / file_path_str
        if file_path.exists():
            symbols = extract_symbols(file_path)
            all_symbols.extend(symbols)

    # Find dependent files (per-language import/require grep)
    dependents = find_dependents(staged_files, repo_root)

    # Run the project's configured test runner (qa_config.json, 12-01)
    config_checkers = load_qa_config(repo_root)
    test_command: list[str] | None
    command_entry = get_test_command(config_checkers)
    test_command = command_entry[1] if command_entry is not None else None
    test_result = run_test(test_command)

    # Determine if breaking change (default: none unless explicitly marked)
    breaks = "none"

    # Format and output
    metadata = format_metadata(all_symbols, breaks, dependents, test_result)
    print(metadata)

    return 0


if __name__ == "__main__":
    sys.exit(main())