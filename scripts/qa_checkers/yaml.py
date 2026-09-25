"""yaml checker plugin — self-registering checker for YAML file validation.

Walks the cwd for *.yaml/*.yml files (excluding pipeline directories),
validates each with yaml.safe_load(), and reports "N files checked, M invalid".

If PyYAML is not installed, fails loudly with "yaml checker: PyYAML not installed".

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

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


def yaml_check() -> tuple[str, int]:
    """Validate all YAML files in cwd and return compressed output.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
        
    Raises:
        SystemExit: If PyYAML is not installed (loud failure).
    """
    # Check if PyYAML is available
    try:
        import yaml
    except ImportError:
        return "yaml checker: PyYAML not installed\n", 1
    
    cwd = Path.cwd()
    
    # Find all *.yaml and *.yml files
    yaml_files = []
    for yaml_file in cwd.rglob("*.yaml"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in yaml_file.relative_to(cwd).parts):
            continue
        yaml_files.append(yaml_file)
    
    for yaml_file in cwd.rglob("*.yml"):
        # Skip excluded directories
        if any(part in EXCLUDE_DIRS for part in yaml_file.relative_to(cwd).parts):
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


# Self-register with the qa_compress registry
import sys
from pathlib import Path as PathlibPath

script_dir = PathlibPath(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("yaml", yaml_check)
