"""json checker plugin — self-registering checker for JSON file validation.

Walks the cwd for *.json files (excluding pipeline directories and qa_config.json),
validates each with json.loads(), and reports "N files checked, M invalid".

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import json
from pathlib import Path


# Deterministic exclusions (fixed contract, no gitignore parsing)
EXCLUDE_DIRS = {
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
        if any(part in EXCLUDE_DIRS for part in json_file.relative_to(cwd).parts):
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


# Self-register with the qa_compress registry
import sys
from pathlib import Path as PathlibPath

script_dir = PathlibPath(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("json", json_check)
