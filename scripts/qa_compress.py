#!/usr/bin/env python3
"""QA-Summary: compact, modular test report. Python reimplementation of qa_compress.sh.

The QA agent reads ONLY this compact result, never raw logs.

Configurability (qa_config.json):
  - The QA-checked project places a committed qa_config.json in the project root
    (cwd when invoked): {"checkers": ["<name>", ...]}.
  - No qa_config.json          -> Default ["pytest"] (backward compatible).
  - Unknown checker name       -> loud FAIL ("unknown checker: <name>"), exit 1.
  - Empty list []              -> explicit opt-out ("no checkers configured
    (explicit opt-out)"), overall: PASS, exit 0.
  - Invalid JSON               -> FAIL with error message, exit 1.
  - This script uses python3 for JSON parsing (python3 is a framework
    requirement, not a project requirement).

Modular checker registry pattern (flat, inline):
  - All checker functions are defined directly in this file (no plugin discovery).
  - Each check function runs the external tool via subprocess.run(), parses
    output with re, and returns (compressed_output: str, exit_code: int).
  - Only CONFIGURED checkers run (serially). Overall status = FAIL as soon as
    ONE checker is non-zero (AND semantics).

Usage: invoke from the project root (cwd = QA-checked project).
Outputs the compact QA package.
"""

from __future__ import annotations

import io
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# --- Checker implementations (inline, no plugin files) ---

def pytest_check() -> tuple[str, int]:
    """Run pytest and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find pytest on PATH (handles .cmd on Windows)
    pytest_exe = shutil.which("pytest")
    if not pytest_exe:
        return "pytest not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [pytest_exe, "--tb=short"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "pytest timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary line: "78 passed in 0.50s" or "1 failed in 0.77s" etc.
    summary_match = re.search(
        r"=+\s*([0-9]+\s+)?[0-9,]*\s*(passed|failed|error|no tests|deselected)",
        output,
    )
    summary = summary_match.group(0) if summary_match else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failed/error lines
        failed_lines = re.findall(r"^(?:FAILED|ERROR) .*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without assertion details)
        short_lines = re.findall(r"^(?:FAILED|ERROR) .*$", output, re.MULTILINE)
        if short_lines:
            compressed += "## short_test_summary\n"
            for line in short_lines[-20:]:  # Last 20
                # Remove assertion details (everything after " - ")
                short = re.sub(r" - .*", "", line)
                compressed += short + "\n"
        
        # Extract assertion lines
        assert_lines = re.findall(r"^\s*>\s*assert.*$", output, re.MULTILINE)
        if assert_lines:
            compressed += "## assertions\n"
            for line in assert_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code


def rspec_check() -> tuple[str, int]:
    """Run rspec and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find rspec on PATH (handles .cmd on Windows)
    rspec_exe = shutil.which("rspec")
    if not rspec_exe:
        return "rspec not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [rspec_exe, "--format", "progress"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "rspec timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary line: "47 examples, 0 failures" or "2 examples, 1 failure"
    summary_match = re.search(r"[0-9]+ examples.*", output)
    summary = summary_match.group(0) if summary_match else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failed test lines: "rspec ./spec/...rb:LINE # description"
        failed_lines = re.findall(r"^rspec \./.*#.*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without description)
        short_lines = re.findall(r"^rspec \./.*#.*$", output, re.MULTILINE)
        if short_lines:
            compressed += "## short_test_summary\n"
            for line in short_lines[-20:]:  # Last 20
                # Remove description (everything after " # ")
                short = re.sub(r" # .*", "", line)
                compressed += short + "\n"
    
    return compressed, exit_code


def jest_check() -> tuple[str, int]:
    """Run jest and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find jest on PATH (handles .cmd on Windows)
    jest_exe = shutil.which("jest")
    if not jest_exe:
        return "jest not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [jest_exe],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "jest timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary line: "Tests:       1 failed, 3 passed, 4 total"
    summary_match = re.search(r"^Tests: .*$", output, re.MULTILINE)
    summary = summary_match.group(0) if summary_match else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failed test lines: "✕ test name (duration)"
        failed_lines = re.findall(r"^✕ .*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code


def gradle_check() -> tuple[str, int]:
    """Run gradle test and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find gradle on PATH (handles .cmd on Windows)
    gradle_exe = shutil.which("gradle")
    if not gradle_exe:
        return "gradle not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [gradle_exe, "test"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "gradle timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary lines: "N tests completed, M failed" and "BUILD SUCCESSFUL/FAILED"
    tests_completed_match = re.search(r"^.*tests completed.*$", output, re.MULTILINE)
    build_match = re.search(r"^BUILD (SUCCESSFUL|FAILED)$", output, re.MULTILINE)
    
    summary_parts = []
    if tests_completed_match:
        summary_parts.append(tests_completed_match.group(0))
    if build_match:
        summary_parts.append(build_match.group(0))
    
    summary = " | ".join(summary_parts) if summary_parts else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failing test identifiers (e.g., "com.example.BoardTest > rendersBoard() FAILED")
        # Exclude the BUILD FAILED line itself
        failed_lines = re.findall(
            r"^.*FAILED$",
            output,
            re.MULTILINE,
        )
        # Filter out "BUILD FAILED" line
        failed_lines = [
            line for line in failed_lines
            if not re.match(r"^BUILD FAILED$", line)
        ]
        
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without details)
        short_lines = re.findall(
            r"^.*FAILED$",
            output,
            re.MULTILINE,
        )
        short_lines = [
            line for line in short_lines
            if not re.match(r"^BUILD FAILED$", line)
        ]
        if short_lines:
            compressed += "## short_test_summary\n"
            for line in short_lines[-20:]:  # Last 20
                # Remove details (everything after " - ")
                short = re.sub(r" - .*", "", line)
                compressed += short + "\n"
    
    return compressed, exit_code


def maven_check() -> tuple[str, int]:
    """Run mvn test and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find mvn on PATH (handles .cmd on Windows)
    mvn_exe = shutil.which("mvn")
    if not mvn_exe:
        return "mvn not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [mvn_exe, "test"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "mvn timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary line: "Tests run: N, Failures: M, Errors: K, Skipped: S"
    summary_match = re.search(r"^Tests run: .*$", output, re.MULTILINE)
    summary = summary_match.group(0) if summary_match else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failure lines: "BoardTest.rendersBoard:15 <<< FAILURE!"
        failed_lines = re.findall(r"^.*<<< FAILURE!.*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without details)
        short_lines = re.findall(r"^.*<<< FAILURE!.*$", output, re.MULTILINE)
        if short_lines:
            compressed += "## short_test_summary\n"
            for line in short_lines[-20:]:  # Last 20
                # Remove details (everything after " - ")
                short = re.sub(r" - .*", "", line)
                compressed += short + "\n"
    
    return compressed, exit_code


# Deterministic exclusions (fixed contract, no gitignore parsing)
_EXCLUDE_DIRS = {
    ".git",
    ".pipeline",
    ".worktrees",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}


def json_check() -> tuple[str, int]:
    """Validate all JSON files in cwd and return compressed output.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    cwd = Path.cwd()
    
    # Find all *.json files
    json_files = []
    for json_file in cwd.rglob("*.json"):
        # Skip excluded directories
        if any(part in _EXCLUDE_DIRS for part in json_file.relative_to(cwd).parts):
            continue
        # Skip qa_config.json itself
        if json_file.name == "qa_config.json":
            continue
        json_files.append(json_file)
    
    # Sort for determinism
    json_files.sort()
    
    total = len(json_files)
    invalid_files = []
    
    for json_file in json_files:
        try:
            with open(json_file, encoding="utf-8") as fh:
                json.load(fh)
        except (json.JSONDecodeError, OSError):
            # Relative path for output
            rel_path = json_file.relative_to(cwd)
            invalid_files.append(str(rel_path))
    
    compressed = f"{total} files checked, {len(invalid_files)} invalid\n"
    
    if invalid_files:
        compressed += "## failed_files\n"
        for path in invalid_files[-20:]:  # Last 20
            compressed += f"INVALID {path}\n"
        return compressed, 1
    
    return compressed, 0


def yaml_check() -> tuple[str, int]:
    """Validate all YAML files in cwd and return compressed output.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Check if PyYAML is available (import inside function for testability)
    try:
        import yaml
    except ImportError:
        return "yaml checker: PyYAML not installed\n", 1
    
    cwd = Path.cwd()
    
    # Find all *.yaml and *.yml files
    yaml_files = []
    for yaml_file in cwd.rglob("*.yaml"):
        # Skip excluded directories
        if any(part in _EXCLUDE_DIRS for part in yaml_file.relative_to(cwd).parts):
            continue
        yaml_files.append(yaml_file)
    
    for yaml_file in cwd.rglob("*.yml"):
        # Skip excluded directories
        if any(part in _EXCLUDE_DIRS for part in yaml_file.relative_to(cwd).parts):
            continue
        yaml_files.append(yaml_file)
    
    # Remove duplicates and sort for determinism
    yaml_files = sorted(set(yaml_files))
    
    total = len(yaml_files)
    invalid_files = []
    
    for yaml_file in yaml_files:
        try:
            with open(yaml_file, encoding="utf-8") as fh:
                yaml.safe_load(fh)
        except (yaml.YAMLError, OSError):
            # Relative path for output
            rel_path = yaml_file.relative_to(cwd)
            invalid_files.append(str(rel_path))
    
    compressed = f"{total} files checked, {len(invalid_files)} invalid\n"
    
    if invalid_files:
        compressed += "## failed_files\n"
        for path in invalid_files[-20:]:  # Last 20
            compressed += f"INVALID {path}\n"
        return compressed, 1
    
    return compressed, 0


# Void tags (self-closing, no closing tag needed)
_VOID_TAGS = frozenset((
    "br", "hr", "img", "input", "meta", "link", "area", "base",
    "col", "embed", "source", "track", "wbr",
))

# Tags excluded from stack checking (implicit close is legal in HTML)
_NO_STACK_TAGS = frozenset(("p",))


class _StackParser(HTMLParser):
    """HTML parser that validates tag stack discipline."""
    
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.stack: list[str] = []
        self.reason: str = ""
    
    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Handle opening tags."""
        if tag not in _VOID_TAGS and tag not in _NO_STACK_TAGS:
            self.stack.append(tag)
    
    def handle_endtag(self, tag: str) -> None:
        """Handle closing tags."""
        if tag in _VOID_TAGS or tag in _NO_STACK_TAGS:
            return
        
        if not self.stack:
            if not self.reason:
                self.reason = f"mismatch: unexpected </{tag}> (stack empty)"
            return
        
        if tag == self.stack[-1]:
            self.stack.pop()
            return
        
        if tag in self.stack:
            # Implicit close: the close tag sits deeper in the stack, so all
            # tags above it were never closed explicitly.
            if not self.reason:
                self.reason = f"unclosed {self.stack[-1]}"
            while self.stack:
                if self.stack.pop() == tag:
                    break
            return
        
        if not self.reason:
            self.reason = f"mismatch: expected </{self.stack[-1]}> got </{tag}>"


def html_check() -> tuple[str, int]:
    """Validate all HTML files in cwd and return compressed output.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    cwd = Path.cwd()
    
    # Find all *.html files
    html_files = []
    for html_file in cwd.rglob("*.html"):
        # Skip excluded directories
        if any(part in _EXCLUDE_DIRS for part in html_file.relative_to(cwd).parts):
            continue
        html_files.append(html_file)
    
    # Sort for determinism
    html_files.sort()
    
    total = len(html_files)
    invalid_files = []
    
    for html_file in html_files:
        try:
            with open(html_file, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
            
            parser = _StackParser()
            parser.feed(text)
            parser.close()
            
            # Check for validation errors
            reason = parser.reason
            if not reason and parser.stack:
                reason = f"unclosed {parser.stack[-1]}"
            
            if reason:
                rel_path = html_file.relative_to(cwd)
                invalid_files.append((str(rel_path), reason))
        
        except Exception as e:
            rel_path = html_file.relative_to(cwd)
            invalid_files.append((str(rel_path), "parse error"))
    
    compressed = f"{total} files checked, {len(invalid_files)} invalid\n"
    
    if invalid_files:
        compressed += "## failed_files\n"
        for path, reason in invalid_files[-20:]:  # Last 20
            compressed += f"INVALID {path} ({reason})\n"
        return compressed, 1
    
    return compressed, 0


# Registry: maps checker name -> checker function
CHECKERS: dict[str, callable] = {
    "pytest": pytest_check,
    "rspec": rspec_check,
    "jest": jest_check,
    "gradle": gradle_check,
    "maven": maven_check,
    "json": json_check,
    "yaml": yaml_check,
    "html": html_check,
}


def _load_config() -> list[str]:
    """Load and parse qa_config.json.
    
    Returns:
        List of configured checker names.
        
    Raises:
        SystemExit: On invalid JSON or missing "checkers" key.
    """
    config_file = Path("qa_config.json")
    
    if not config_file.exists():
        # Default: ["pytest"]
        return ["pytest"]
    
    try:
        with open(config_file, encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError as exc:
        print(f"qa_config.json: invalid JSON: {exc}", file=sys.stderr)
        sys.exit(1)
    except OSError as exc:
        print(f"qa_config.json: unreadable: {exc}", file=sys.stderr)
        sys.exit(1)
    
    if not isinstance(data, dict) or "checkers" not in data:
        print('qa_config.json: missing key "checkers"', file=sys.stderr)
        sys.exit(1)
    
    names = data["checkers"]
    if not isinstance(names, list) or not all(isinstance(n, str) for n in names):
        print('qa_config.json: "checkers" must be a list of strings', file=sys.stderr)
        sys.exit(1)
    
    return names


def _validate_configured_checkers(configured: list[str]) -> None:
    """Validate that all configured checker names are registered.
    
    Raises:
        SystemExit: If an unknown checker is configured.
    """
    for name in configured:
        if name not in CHECKERS:
            registered = ", ".join(sorted(CHECKERS.keys()))
            print(
                f"unknown checker: {name} (registered: {registered})",
                file=sys.stderr,
            )
            sys.exit(1)


def main() -> int:
    """Main entry point."""
    # Load configuration
    configured = _load_config()
    
    # Validate configured checkers
    _validate_configured_checkers(configured)
    
    # Handle explicit opt-out
    if not configured:
        print("no checkers configured (explicit opt-out)")
        print("---")
        print("overall: PASS")
        return 0
    
    # Run checkers
    print(f"# QA-Testsummary ({datetime.now().strftime('%H:%M:%S')})")
    print("---")
    
    overall_exit = 0
    for name in configured:
        fn = CHECKERS[name]
        output, exit_code = fn()
        
        print(f"## {name} (exit: {exit_code})")
        print(output, end="")
        
        if exit_code != 0:
            overall_exit = 1
    
    print("---")
    print(f"overall: {'FAIL' if overall_exit else 'PASS'}")
    
    return overall_exit


if __name__ == "__main__":
    sys.exit(main())
