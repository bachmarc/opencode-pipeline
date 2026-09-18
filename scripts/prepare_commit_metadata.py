#!/usr/bin/env python3
"""Prepare commit metadata from staged changes.

Analyzes git diff --cached to extract:
- Changed file names
- Changed export symbols (Python: functions/classes via AST, other: file-level)
- Dependent files (grep for imports of changed modules)
- Test result (pytest --tb=no -q)

Outputs formatted metadata string:
  symbols: ... | breaks: none|breaking | affects: ... | tests: ...

Exit code: 0 always (informational)
"""

from __future__ import annotations

import ast
import re
import subprocess
import sys
from pathlib import Path


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


def extract_symbols(file_path: Path) -> list[str]:
    """Extract changed symbols from a file."""
    if file_path.suffix == ".py":
        return extract_python_symbols(file_path)
    
    # For non-Python files, use filename as symbol
    return [file_path.stem]


def find_dependents(changed_files: list[str], repo_root: Path) -> list[str]:
    """Find files that import changed modules."""
    dependents = set()
    
    # Extract module names from changed files
    modules = set()
    for file_path in changed_files:
        if file_path.endswith(".py"):
            # Convert file path to module name
            module_name = file_path.replace("/", ".").replace("\\", ".").replace(".py", "")
            modules.add(module_name)
            # Also add just the filename without extension
            modules.add(Path(file_path).stem)
    
    if not modules:
        return []
    
    # Search for imports of these modules
    for module in modules:
        # Escape special regex characters
        escaped_module = re.escape(module)
        pattern = rf"(from|import)\s+{escaped_module}(\s|$|\.)"
        
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


def run_pytest() -> str:
    """Run pytest and return result summary."""
    result = subprocess.run(
        ["python", "-m", "pytest", "--tb=no", "-q"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    # Extract summary line
    lines = result.stdout.strip().split("\n")
    if lines:
        # Return last non-empty line (usually the summary)
        for line in reversed(lines):
            if line.strip():
                return line.strip()
    
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
    
    # Extract symbols from changed files
    all_symbols = []
    for file_path_str in staged_files:
        file_path = repo_root / file_path_str
        if file_path.exists():
            symbols = extract_symbols(file_path)
            all_symbols.extend(symbols)
    
    # Find dependent files
    dependents = find_dependents(staged_files, repo_root)
    
    # Run pytest
    test_result = run_pytest()
    
    # Determine if breaking change
    # Simple heuristic: if symbols changed, it might be breaking
    breaks = "none"
    if all_symbols:
        # Could be breaking if we're modifying exports
        # For now, default to "none" unless explicitly marked
        breaks = "none"
    
    # Format and output
    metadata = format_metadata(all_symbols, breaks, dependents, test_result)
    print(metadata)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
