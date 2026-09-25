"""jest checker plugin — self-registering checker for jest test runs.

Runs jest, extracts the "Tests:" summary line, and on failure extracts ✕ lines.

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import re
import subprocess


def jest_check() -> tuple[str, int]:
    """Run jest and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    try:
        result = subprocess.run(
            ["jest"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "jest not found on PATH\n", 1
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


# Self-register with the qa_compress registry
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("jest", jest_check)
