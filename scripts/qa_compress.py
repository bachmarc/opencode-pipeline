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

Available checkers (register in qa_config.json):
  - pytest: Python test framework
  - rspec: Ruby test framework (uses `bundle exec rspec`)
  - jest: JavaScript/TypeScript test framework
  - eslint: JavaScript/TypeScript linting
  - tsc: TypeScript type checking
  - prettier: Code formatting check (JavaScript/TypeScript)
  - npm-audit: npm security audit
  - gradle: Java/Kotlin build tool with tests
  - maven: Java build tool with tests
  - json: JSON schema validation
  - yaml: YAML schema validation
  - html: HTML tag stack validation
  - rubocop: Ruby linting (tries `bundle exec rubocop`, falls back to `rubocop`)
  - checkstyle: Java static analysis (tries gradlew, mvn, then binary)
  - mypy: Python type checker
  - ruff: Python linter
  - black: Python code formatter

Modular checker registry pattern (flat, inline):
  - All checker functions are defined directly in this file (no plugin discovery).
  - Each check function runs the external tool via subprocess.run(), parses
    output with re, and returns (compressed_output: str, exit_code: int).
  - Only CONFIGURED checkers run (serially). Overall status = FAIL as soon as
    ONE checker is non-zero (AND semantics).

Process checkers (Tier D, OFF by default — projects opt in per profile):
  - worktree_discipline: derives the story id from the CURRENT git branch
    (feature/<story-id>-<slug>; qa_config.json process_checker.story_id as
    fallback override for out-of-worktree runs) and requires a registered
    worktree under process_checker.worktree_root (default ".worktrees",
    resolved against the main worktree) that has the story branch checked
    out. Detects work done outside the story worktree.
  - metadata_affects: validates commit metadata across ALL branch commits
    since the merge base with the default branch (main, fallback master) —
    every affects: path must exist in the repo, and every changed src/ or
    tests/ file must be declared in some commit's symbols:/affects: values
    (docs/planning-only branches pass without declarations).
  - Config: optional qa_config.json block "process_checker" with string keys
    "story_id" and "worktree_root"; unknown keys inside the block fail
    validation like unknown checker names.

Fast mode (--fast flag):
  - Detects changed files via `git diff main..<branch> --name-only`.
  - Falls back to `git diff HEAD~1 --name-only` if not on a feature branch.
  - Maps changed files to test modules by name convention:
    * scripts/foo.py         -> tests/test_foo.py
    * plugins/guards/foo.ts  -> tests/test_foo.py (dashes to underscores)
    * plugins/foo.ts         -> tests/test_foo.py
  - Returns only test files that exist. If no matches, falls back to full run.
  - Output: "[fast mode] running: tests/test_foo.py tests/test_bar.py"

Usage: invoke from the project root (cwd = QA-checked project).
  - Full run: python scripts/qa_compress.py
  - Fast run: python scripts/qa_compress.py --fast
Outputs the compact QA package.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import shutil
import subprocess
import sys
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path

# Ensure UTF-8 output on Windows (skip in test environments)
if sys.platform == "win32" and "pytest" not in sys.modules:
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except (AttributeError, ValueError):
        # In test environments or when stdout is already wrapped, skip
        pass

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


def eslint_check() -> tuple[str, int]:
    """Run eslint and return compressed output with exit code.
    
    Tries local node_modules/.bin/eslint first, then eslint on PATH, then npx.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Try local node_modules/.bin first
    eslint_exe = Path("node_modules") / ".bin" / "eslint"
    cmd = None
    
    if eslint_exe.exists():
        cmd = [str(eslint_exe)]
    else:
        # Try PATH (for test fakes)
        exe = shutil.which("eslint")
        if exe:
            cmd = [exe]
        else:
            # Try npx as fallback
            npx_exe = shutil.which("npx")
            if npx_exe:
                cmd = [npx_exe, "eslint", "--no-install"]
    
    if not cmd:
        return "eslint not found (checked: node_modules/.bin/eslint, npx, PATH)\n", 1
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "eslint timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Count errors: look for lines containing "error" or pattern like "X problems"
    # ESLint output: "file:line:col: message (rule-name)"
    error_lines = [line for line in output.split("\n") if line.strip() and ":" in line]
    error_count = len(error_lines)
    
    # Also check for summary line like "3 errors in 2 files"
    summary_match = re.search(r"(\d+)\s+errors?", output)
    if summary_match:
        error_count = int(summary_match.group(1))
    
    if exit_code == 0:
        return "eslint: 0 errors\n", 0
    
    compressed = f"eslint: {error_count} errors\n"
    if error_lines:
        compressed += "## errors\n"
        for line in error_lines[:20]:  # First 20
            compressed += line + "\n"
    
    return compressed, exit_code


def tsc_check() -> tuple[str, int]:
    """Run TypeScript compiler check (--noEmit) and return compressed output with exit code.
    
    Tries local node_modules/.bin/tsc first, then tsc on PATH, then npx.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Try local node_modules/.bin first
    tsc_exe = Path("node_modules") / ".bin" / "tsc"
    cmd = None
    
    if tsc_exe.exists():
        cmd = [str(tsc_exe), "--noEmit"]
    else:
        # Try PATH (for test fakes)
        exe = shutil.which("tsc")
        if exe:
            cmd = [exe, "--noEmit"]
        else:
            # Try npx as fallback
            npx_exe = shutil.which("npx")
            if npx_exe:
                cmd = [npx_exe, "tsc", "--noEmit"]
    
    if not cmd:
        return "tsc not found\n", 1
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "tsc timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Count errors: tsc outputs "file(line,col): error TSxxxx: message"
    error_lines = [line for line in output.split("\n") if "error TS" in line]
    error_count = len(error_lines)
    
    if exit_code == 0:
        return "tsc: 0 errors\n", 0
    
    compressed = f"tsc: {error_count} errors\n"
    if error_lines:
        compressed += "## errors\n"
        for line in error_lines[:20]:  # First 20
            compressed += line + "\n"
    
    return compressed, exit_code


def prettier_check() -> tuple[str, int]:
    """Run Prettier in check mode and return compressed output with exit code.
    
    Tries local node_modules/.bin/prettier first, then prettier on PATH, then npx.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Try local node_modules/.bin first
    prettier_exe = Path("node_modules") / ".bin" / "prettier"
    cmd = None
    
    if prettier_exe.exists():
        cmd = [str(prettier_exe), "--check", "."]
    else:
        # Try PATH (for test fakes)
        exe = shutil.which("prettier")
        if exe:
            cmd = [exe, "--check", "."]
        else:
            # Try npx as fallback
            npx_exe = shutil.which("npx")
            if npx_exe:
                cmd = [npx_exe, "prettier", "--check", "."]
    
    if not cmd:
        return "prettier not found\n", 1
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "prettier timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    if exit_code == 0:
        return "prettier: all files formatted\n", 0
    
    # Parse unformatted files: prettier lists them line by line
    file_lines = [line.strip() for line in output.split("\n") if line.strip() and not line.startswith("--")]
    # Filter out summary lines
    file_lines = [line for line in file_lines if not re.match(r"^\d+\s+", line)]
    
    compressed = f"prettier: {len(file_lines)} unformatted files\n"
    if file_lines:
        compressed += "## unformatted_files\n"
        for line in file_lines[:20]:  # First 20
            compressed += line + "\n"
    
    return compressed, exit_code


def npm_audit_check() -> tuple[str, int]:
    """Run npm audit with high severity threshold and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    npm_exe = shutil.which("npm")
    if not npm_exe:
        return "npm not found\n", 1
    
    try:
        result = subprocess.run(
            [npm_exe, "audit", "--audit-level=high"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "npm audit timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary: "X vulnerabilities" or similar
    summary_match = re.search(r"(\d+)\s+vulnerabilities?", output)
    vuln_count = int(summary_match.group(1)) if summary_match else 0
    
    if exit_code == 0:
        return "npm-audit: 0 vulnerabilities\n", 0
    
    compressed = f"npm-audit: {vuln_count} vulnerabilities\n"
    
    # Extract vulnerability lines (usually marked with "| Name" or package names)
    vuln_lines = [line for line in output.split("\n") if line.strip() and ("|" in line or "found" in line.lower())]
    if vuln_lines:
        compressed += "## vulnerabilities\n"
        for line in vuln_lines[:20]:  # First 20
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


def rubocop_check() -> tuple[str, int]:
    """Run rubocop and return compressed output with exit code.
    
    Tries ``bundle exec rubocop`` first (Gemfile-locked version), falls back
    to ``rubocop`` on PATH. If neither found: "rubocop not found\n", exit 1.
    On success: "rubocop: 0 offenses\n".
    On failure: offense count + first 20 offense lines.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Try bundle exec rubocop first (preferred for Gemfile-locked version)
    rubocop_exe = None
    rubocop_args = []
    
    bundle_exe = shutil.which("bundle")
    if bundle_exe:
        # Try bundle exec rubocop first
        try:
            result = subprocess.run(
                [bundle_exe, "exec", "rubocop", "--version"],
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
            if result.returncode == 0:
                # bundle exec rubocop exists and works
                rubocop_args = [bundle_exe, "exec", "rubocop"]
                rubocop_exe = bundle_exe
        except subprocess.TimeoutExpired:
            pass
    
    # Fall back to rubocop on PATH if bundle exec didn't work
    if not rubocop_exe:
        rubocop_exe = shutil.which("rubocop")
        if not rubocop_exe:
            return "rubocop not found\n", 1
        rubocop_args = [rubocop_exe]
    
    try:
        result = subprocess.run(
            rubocop_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "rubocop timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract offense count: "X files inspected, Y offenses detected"
    # or "X files inspected, no offenses detected"
    summary_match = re.search(r"(\d+) files inspected, (no offenses|(\d+) offenses)", output)
    
    if summary_match:
        if summary_match.group(2) == "no offenses":
            compressed = "rubocop: 0 offenses\n"
        else:
            offense_count = summary_match.group(3)
            compressed = f"rubocop: {offense_count} offenses\n"
    else:
        compressed = "rubocop: <no summary>\n"
    
    if exit_code != 0:
        # Extract offense lines: "path/to/file.rb:LINE:COL: [LETTER]: Message"
        offense_lines = re.findall(r"^.*\.rb:\d+:\d+:", output, re.MULTILINE)
        if offense_lines:
            compressed += "## offenses\n"
            for line in offense_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code


def checkstyle_check() -> tuple[str, int]:
    """Run Checkstyle and return compressed output with exit code.
    
    Tries ``./gradlew checkstyleMain checkstyleTest`` first (if gradlew present),
    then ``mvn checkstyle:check``, then ``checkstyle`` on PATH.
    Not found/not applicable: "checkstyle not found (no gradlew, mvn, or checkstyle binary)\n", exit 1.
    On success: "checkstyle: 0 violations\n".
    On failure: violation count + first 20 violation lines.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Try gradlew first (locally or on PATH)
    cwd = Path.cwd()
    gradlew_local = cwd / "gradlew"
    checkstyle_args = []
    
    if gradlew_local.exists():
        checkstyle_args = [str(gradlew_local), "checkstyleMain", "checkstyleTest"]
    else:
        # Try gradlew on PATH
        gradlew_exe = shutil.which("gradlew")
        if gradlew_exe:
            checkstyle_args = [gradlew_exe, "checkstyleMain", "checkstyleTest"]
        else:
            # Try mvn on PATH
            mvn_exe = shutil.which("mvn")
            if mvn_exe:
                checkstyle_args = [mvn_exe, "checkstyle:check"]
            else:
                # Try checkstyle on PATH
                checkstyle_exe = shutil.which("checkstyle")
                if checkstyle_exe:
                    checkstyle_args = [checkstyle_exe]
                else:
                    return "checkstyle not found (no gradlew, mvn, or checkstyle binary)\n", 1
    
    try:
        result = subprocess.run(
            checkstyle_args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "checkstyle timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # For gradle/gradlew: look for "[ERROR]" lines (violations)
    # For mvn: look for "[ERROR]" lines
    # Count violations
    error_lines = re.findall(r"^\[ERROR\]", output, re.MULTILINE)
    violation_count = len(error_lines)
    
    if exit_code == 0 or violation_count == 0:
        compressed = "checkstyle: 0 violations\n"
    else:
        compressed = f"checkstyle: {violation_count} violations\n"
    
    if exit_code != 0 and violation_count > 0:
        # Extract violation lines: "[ERROR] /path/...java:LINE: Message"
        violations = re.findall(r"^\[ERROR\] .*$", output, re.MULTILINE)
        if violations:
            compressed += "## violations\n"
            for line in violations[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code


def mypy_check() -> tuple[str, int]:
    """Run mypy type checker and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find mypy on PATH
    mypy_exe = shutil.which("mypy")
    if not mypy_exe:
        return "mypy not found\n", 1
    
    # Determine target: use 'src/' if it exists, else '.'
    target = "src" if Path("src").is_dir() else "."
    
    try:
        result = subprocess.run(
            [mypy_exe, target],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "mypy timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract error count from "Found N errors in M files" or similar
    error_count_match = re.search(r"Found (\d+) errors?", output)
    error_count = error_count_match.group(1) if error_count_match else "0"
    
    if exit_code == 0:
        compressed = f"mypy: {error_count} errors\n"
    else:
        # Extract error lines: "FILE:LINE:COL: error: MESSAGE"
        error_lines = re.findall(r"^[^:]+:\d+:\d+: error: .*$", output, re.MULTILINE)
        
        compressed = f"mypy: {error_count} errors found\n"
        if error_lines:
            compressed += "## type_errors\n"
            for line in error_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code



def ruff_check() -> tuple[str, int]:
    """Run ruff linter and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find ruff on PATH
    ruff_exe = shutil.which("ruff")
    if not ruff_exe:
        return "ruff not found\n", 1
    
    try:
        result = subprocess.run(
            [ruff_exe, "check", "."],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "ruff timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract error count from "Found N errors" or similar
    error_count_match = re.search(r"Found (\d+) errors?", output)
    error_count = error_count_match.group(1) if error_count_match else "0"
    
    if exit_code == 0:
        compressed = f"ruff: {error_count} violations\n"
    else:
        # Extract violation lines: "FILE:LINE:COL: CODE MESSAGE"
        violation_lines = re.findall(r"^[^:]+:\d+:\d+: [A-Z]\d+ .*$", output, re.MULTILINE)
        
        compressed = f"ruff: {error_count} violations found\n"
        if violation_lines:
            compressed += "## violations\n"
            for line in violation_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code



def black_check() -> tuple[str, int]:
    """Run black formatter check and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find black on PATH
    black_exe = shutil.which("black")
    if not black_exe:
        return "black not found\n", 1
    
    try:
        result = subprocess.run(
            [black_exe, "--check", "."],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        return "black timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    if exit_code == 0:
        compressed = "black: all files formatted\n"
    else:
        # Extract "would reformat" lines
        reformat_lines = re.findall(r"^would reformat .*$", output, re.MULTILINE)
        
        compressed = "black: files would be reformatted\n"
        if reformat_lines:
            compressed += "## reformattable_files\n"
            for line in reformat_lines[-20:]:  # Last 20
                compressed += line + "\n"
    
    return compressed, exit_code


# --- Process checkers (Tier D): inspect git state, no tool binaries needed ---

# Allowed keys in the optional qa_config.json "process_checker" block.
_PROCESS_CHECKER_KEYS = ("story_id", "worktree_root")
_DEFAULT_WORKTREE_ROOT = ".worktrees"


def _git_out(*args: str) -> str | None:
    """Run a git command in the project cwd and return stripped stdout.

    Returns:
        Stripped stdout on exit code 0, else None (including timeouts and
        missing git binary).
    """
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def _read_process_checker_config() -> dict[str, str]:
    """Re-read the optional qa_config.json "process_checker" block.

    ``_load_config()`` already validated this block (unknown keys and
    non-string values exit loudly), so a silent fallback to an empty dict is
    safe here.

    Returns:
        The process_checker mapping, or {} when absent or unreadable.
    """
    try:
        with open(Path("qa_config.json"), encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(data, dict):
        return {}
    block = data.get("process_checker")
    return dict(block) if isinstance(block, dict) else {}


def _fail_json(reason: str) -> str:
    """Format a checker FAIL verdict with reason as one JSON line."""
    return json.dumps({"result": "FAIL", "reason": reason}) + "\n"


def _parse_commit_metadata(message: str) -> dict[str, str]:
    """Extract the pipe-separated key-value metadata segments from a message.

    Convention (scripts/prepare_commit_metadata.py): a body line like
    ``symbols: a, b | breaks: none | affects: x y | tests: N passed``.
    First occurrence of a key wins; unknown keys are ignored.

    Args:
        message: Full commit message (subject + body).

    Returns:
        Mapping of recognized keys (symbols/affects/breaks/tests) to their
        raw string values.
    """
    meta: dict[str, str] = {}
    for line in message.splitlines():
        for chunk in line.split("|"):
            match = re.match(r"\s*(symbols|affects|breaks|tests)\s*:\s*(.+?)\s*$", chunk)
            if match and match.group(1) not in meta:
                meta[match.group(1)] = match.group(2)
    return meta


def worktree_discipline() -> tuple[str, int]:
    """Check story worktree discipline (Tier D).

    The story id is derived from the CURRENT git branch
    (``feature/<story-id>-<slug>``); the optional ``process_checker.story_id``
    config key is a fallback override for out-of-worktree runs. Rule:
    ``git worktree list --porcelain`` must contain a worktree whose
    checked-out branch matches the story branch AND whose path is under
    ``<worktree_root>/<story-id>-*`` (``worktree_root`` defaults to
    ``.worktrees``, resolved against the main worktree).

    FAIL reasons: no worktree registered for the story / story branch checked
    out outside the expected worktree root.

    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    branch = _git_out("rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        return _fail_json("cannot determine current git branch"), 1

    config = _read_process_checker_config()
    story_id: str | None = None
    branch_match = re.match(r"^feature/(\d+-\d+)-", branch)
    if branch_match:
        story_id = branch_match.group(1)
    if story_id is None:
        # Fallback override for out-of-worktree runs (e.g. QA on the main
        # checkout with an explicit story id).
        story_id = config.get("story_id")
    if not story_id:
        return _fail_json(
            f"cannot derive story id from branch '{branch}' "
            "(expected feature/<story-id>-<slug>); set process_checker.story_id "
            "override in qa_config.json"
        ), 1

    worktree_root = config.get("worktree_root", _DEFAULT_WORKTREE_ROOT)
    listing = _git_out("worktree", "list", "--porcelain")
    if listing is None:
        return _fail_json("git worktree list failed"), 1

    # Parse porcelain entries: worktree <path> / branch refs/heads/<name>.
    entries: list[tuple[str, str | None]] = []
    current_path: str | None = None
    current_branch: str | None = None
    for line in listing.splitlines():
        if line.startswith("worktree "):
            if current_path is not None:
                entries.append((current_path, current_branch))
            current_path = line[len("worktree "):].strip()
            current_branch = None
        elif line.startswith("branch ") and current_path is not None:
            current_branch = line[len("branch "):].strip().removeprefix("refs/heads/")
    if current_path is not None:
        entries.append((current_path, current_branch))

    if not entries:
        return _fail_json("no worktrees registered"), 1

    # The main worktree is always listed first; worktree_root resolves
    # against it.
    expected_root = Path(entries[0][0]) / worktree_root
    branch_pattern = re.compile(rf"^feature/{re.escape(story_id)}(-|$)")
    matches = [
        (path, entry_branch)
        for path, entry_branch in entries
        if entry_branch is not None and branch_pattern.match(entry_branch)
    ]

    if not matches:
        return _fail_json(
            f"no worktree registered for story {story_id}: no worktree has a "
            f"branch matching feature/{story_id}-* checked out"
        ), 1

    worktree_path, checked_out_branch = matches[0]
    candidate = Path(worktree_path)
    if not (
        candidate.is_relative_to(expected_root)
        and candidate.name.startswith(f"{story_id}-")
    ):
        return _fail_json(
            f"story branch '{checked_out_branch}' checked out outside expected "
            f"worktree root {expected_root}/{story_id}-* (worktree: {worktree_path})"
        ), 1

    output = json.dumps(
        {"result": "PASS", "branch": checked_out_branch, "worktree": worktree_path},
        sort_keys=True,
    ) + "\n"
    return output, 0


def metadata_affects() -> tuple[str, int]:
    """Check commit metadata consistency for the whole story branch (Tier D).

    Scope: ALL commits between the merge base with the default branch (main,
    fallback master) and HEAD — not just the last commit — so fix-loop
    follow-ups stay covered. Rules:

    1. Every path listed in a commit's ``affects:`` must exist in the repo
       (the sentinels ``nothing``/``none`` are skipped).
    2. Every changed ``src/``/``tests/`` file across the branch (via
       ``git diff --name-only <merge-base>..HEAD``) must be declared in some
       commit's ``symbols:``/``affects:`` values — OR the branch is
       docs/planning-only (no code paths changed) and passes without
       declarations.

    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    branch = _git_out("rev-parse", "--abbrev-ref", "HEAD")
    if branch is None:
        return _fail_json("cannot determine current git branch"), 1

    merge_base: str | None = None
    for default_branch in ("main", "master"):
        merge_base = _git_out("merge-base", default_branch, "HEAD")
        if merge_base is not None:
            break
    if merge_base is None:
        return _fail_json("cannot determine merge base (main/master merge-base failed)"), 1

    log_output = _git_out("log", f"{merge_base}..HEAD", "--format=%x1f%s%x1f%B%x1e")
    if log_output is None:
        return _fail_json("git log failed"), 1
    diff_output = _git_out("diff", "--name-only", f"{merge_base}..HEAD")
    if diff_output is None:
        return _fail_json("git diff failed"), 1

    changed_files = [line.strip() for line in diff_output.splitlines() if line.strip()]
    code_files = [
        path for path in changed_files
        if path.startswith("src/") or path.startswith("tests/")
    ]

    # Parse the metadata segments of EVERY branch commit (multi-commit scope).
    symbols_values: list[str] = []
    affects_values: list[str] = []
    for record in log_output.split("\x1e"):
        parts = record.split("\x1f")
        if len(parts) < 2:
            continue
        subject = parts[1]
        body = parts[2] if len(parts) > 2 else ""
        meta = _parse_commit_metadata(subject + "\n" + body)
        if "symbols" in meta:
            symbols_values.append(meta["symbols"])
        if "affects" in meta:
            affects_values.append(meta["affects"])

    errors: list[str] = []
    checks = 0

    # Rule 1: every declared affects path must exist in the repo.
    for value in affects_values:
        for token in re.split(r"[\s,]+", value):
            token = token.strip()
            if not token or token in ("nothing", "none"):
                continue
            checks += 1
            if not Path(token).exists():
                errors.append(f"declared affects path does not exist: {token}")

    # Rule 2: changed src//tests files must be declared somewhere on the branch.
    declared = " ".join(symbols_values + affects_values)
    for path in code_files:
        checks += 1
        if path not in declared:
            errors.append(
                f"changed code file not declared in any commit's "
                f"symbols:/affects:: {path}"
            )

    if errors:
        return json.dumps({"result": "FAIL", "errors": errors}) + "\n", 1

    output = json.dumps({"result": "PASS", "checks": checks}, sort_keys=True) + "\n"
    return output, 0


# Registry: maps checker name -> checker function


# Registry: maps checker name -> checker function
CHECKERS: dict[str, callable] = {
    "pytest": pytest_check,
    "rspec": rspec_check,
    "jest": jest_check,
    "eslint": eslint_check,
    "tsc": tsc_check,
    "prettier": prettier_check,
    "npm-audit": npm_audit_check,
    "gradle": gradle_check,
    "maven": maven_check,
    "json": json_check,
    "yaml": yaml_check,
    "html": html_check,
    "rubocop": rubocop_check,
    "checkstyle": checkstyle_check,
    "mypy": mypy_check,
    "ruff": ruff_check,
    "black": black_check,
    "worktree_discipline": worktree_discipline,
    "metadata_affects": metadata_affects,
}


def _load_config() -> tuple[list[str], object]:
    """Load and parse qa_config.json.

    Returns:
        Tuple of (configured checker names, raw "process_checker" block).
        The block is passed through UNVALIDATED — call
        ``_validate_configured_checkers()`` on it; it is None when absent.

    Raises:
        SystemExit: On invalid JSON or missing "checkers" key.
    """
    config_file = Path("qa_config.json")

    if not config_file.exists():
        # Default: ["pytest"]
        return ["pytest"], None

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

    return names, data.get("process_checker")


def _validate_process_checker_block(block: object) -> None:
    """Validate the optional qa_config.json "process_checker" block.

    Allowed keys: "story_id" and "worktree_root", both strings (story_id is
    a fallback override for out-of-worktree runs, worktree_root defaults to
    ".worktrees"). Unknown keys fail validation like unknown checker names.

    Raises:
        SystemExit: On non-object block, unknown key, or non-string value.
    """
    if block is None:
        return
    if not isinstance(block, dict):
        print('qa_config.json: "process_checker" must be an object', file=sys.stderr)
        sys.exit(1)
    for key, value in block.items():
        if key not in _PROCESS_CHECKER_KEYS:
            allowed = ", ".join(_PROCESS_CHECKER_KEYS)
            print(
                f"unknown process_checker key: {key} (allowed: {allowed})",
                file=sys.stderr,
            )
            sys.exit(1)
        if not isinstance(value, str):
            print(
                f'qa_config.json: "process_checker.{key}" must be a string',
                file=sys.stderr,
            )
            sys.exit(1)


def _validate_configured_checkers(
    configured: list[str],
    process_checker: object = None,
) -> None:
    """Validate that all configured checker names are registered.

    Also validates the optional process_checker block (unknown keys inside
    it fail like unknown checker names).

    Raises:
        SystemExit: If an unknown checker or process_checker key is configured.
    """
    for name in configured:
        if name not in CHECKERS:
            registered = ", ".join(sorted(CHECKERS.keys()))
            print(
                f"unknown checker: {name} (registered: {registered})",
                file=sys.stderr,
            )
            sys.exit(1)
    _validate_process_checker_block(process_checker)


def get_changed_test_modules(repo_root: Path) -> list[str]:
    """Return test module paths for files changed on this branch vs main.
    
    Uses git diff main..HEAD --name-only to find changed files.
    Maps by name convention:
      scripts/foo.py         -> tests/test_foo.py
      plugins/guards/foo.ts  -> tests/test_foo.py  (foo with dashes -> underscores)
      plugins/foo.ts         -> tests/test_foo.py
    
    Returns only paths that actually exist. Empty list = fallback to full run.
    Falls back to git diff HEAD~1 --name-only if not on a feature branch.
    
    Args:
        repo_root: Path to the repository root.
    
    Returns:
        List of test file paths (as strings) that exist and match changed files.
        Empty list if no matches found.
    """
    # Try to get changed files via git diff main..HEAD
    try:
        result = subprocess.run(
            ["git", "diff", "main..HEAD", "--name-only"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=10,
        )
        
        if result.returncode != 0:
            # Not on a feature branch, try HEAD~1
            result = subprocess.run(
                ["git", "diff", "HEAD~1", "--name-only"],
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                timeout=10,
            )
        
        if result.returncode != 0:
            # git diff failed, return empty list
            return []
        
        changed_files = result.stdout.strip().split("\n")
    except (subprocess.TimeoutExpired, FileNotFoundError):
        # git not available or timed out
        return []
    
    # Map changed files to test modules
    test_modules = set()
    
    for file_path in changed_files:
        if not file_path.strip():
            continue
        
        # Normalize path separators
        file_path = file_path.replace("\\", "/")
        
        # Map scripts/foo.py -> tests/test_foo.py
        if file_path.startswith("scripts/") and file_path.endswith(".py"):
            base_name = Path(file_path).stem
            test_file = repo_root / "tests" / f"test_{base_name}.py"
            if test_file.exists():
                test_modules.add(str(test_file))
        
        # Map plugins/guards/foo.ts -> tests/test_foo.py (dashes to underscores)
        elif file_path.startswith("plugins/guards/") and file_path.endswith(".ts"):
            base_name = Path(file_path).stem
            # Replace dashes with underscores
            base_name = base_name.replace("-", "_")
            test_file = repo_root / "tests" / f"test_{base_name}.py"
            if test_file.exists():
                test_modules.add(str(test_file))
        
        # Map plugins/foo.ts -> tests/test_foo.py (dashes to underscores)
        elif file_path.startswith("plugins/") and file_path.endswith(".ts"):
            # Skip if it's in plugins/guards (already handled above)
            if not file_path.startswith("plugins/guards/"):
                base_name = Path(file_path).stem
                # Replace dashes with underscores
                base_name = base_name.replace("-", "_")
                test_file = repo_root / "tests" / f"test_{base_name}.py"
                if test_file.exists():
                    test_modules.add(str(test_file))
    
    return sorted(list(test_modules))


def main() -> int:
    """Main entry point."""
    # Parse arguments
    parser = argparse.ArgumentParser(
        description="QA-Summary: compact, modular test report"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Fast mode: run only tests for changed files (git diff main..HEAD)",
    )
    args = parser.parse_args()
    
    # Load configuration
    configured, process_checker = _load_config()

    # Validate configured checkers (+ optional process_checker block)
    _validate_configured_checkers(configured, process_checker)
    
    # Handle explicit opt-out
    if not configured:
        print("no checkers configured (explicit opt-out)")
        print("---")
        print("overall: PASS")
        return 0
    
    # Handle fast mode
    fast_mode_args = []
    if args.fast:
        repo_root = Path.cwd()
        changed_test_modules = get_changed_test_modules(repo_root)
        
        if changed_test_modules:
            # Run only the changed test modules
            print(f"[fast mode] running: {' '.join(changed_test_modules)}")
            fast_mode_args = changed_test_modules
        else:
            # No matching test modules, fall back to full run
            print("[fast mode] no matching test modules found, falling back to full run")
    
    # Run checkers
    print(f"# QA-Testsummary ({datetime.now().strftime('%H:%M:%S')})")
    print("---")
    
    overall_exit = 0
    for name in configured:
        fn = CHECKERS[name]
        
        # For pytest checker in fast mode, pass the test modules as arguments
        if name == "pytest" and fast_mode_args:
            output, exit_code = _pytest_check_with_args(fast_mode_args)
        else:
            output, exit_code = fn()
        
        print(f"## {name} (exit: {exit_code})")
        print(output, end="")
        
        if exit_code != 0:
            overall_exit = 1
    
    print("---")
    print(f"overall: {'FAIL' if overall_exit else 'PASS'}")
    
    return overall_exit


def _pytest_check_with_args(test_modules: list[str]) -> tuple[str, int]:
    """Run pytest with specific test modules and return compressed output.
    
    Args:
        test_modules: List of test file paths to run.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    # Find pytest on PATH (handles .cmd on Windows)
    pytest_exe = shutil.which("pytest")
    if not pytest_exe:
        return "pytest not found on PATH\n", 1
    
    try:
        result = subprocess.run(
            [pytest_exe, "--tb=short"] + test_modules,
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


if __name__ == "__main__":
    sys.exit(main())
