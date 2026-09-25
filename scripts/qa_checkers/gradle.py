"""gradle checker plugin — self-registering checker for gradle test runs.

Runs gradle test, extracts the "N tests completed" and "BUILD SUCCESSFUL/FAILED" summary,
and on failure extracts FAILED test identifiers (not the BUILD line).

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import re
import subprocess


def gradle_check() -> tuple[str, int]:
    """Run gradle test and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    try:
        result = subprocess.run(
            ["gradle", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "gradle not found on PATH\n", 1
    except subprocess.TimeoutExpired:
        return "gradle timed out\n", 1
    
    output = result.stdout + result.stderr
    exit_code = result.returncode
    
    # Extract summary line: "N tests completed, M failed" or "BUILD SUCCESSFUL/FAILED"
    summary_match = re.search(
        r"tests completed|BUILD (SUCCESSFUL|FAILED)",
        output,
    )
    summary = summary_match.group(0) if summary_match else "<no summary line>"
    
    compressed = f"summary: {summary}\n"
    
    if exit_code != 0:
        # Extract failing test identifiers (e.g., "com.example.BoardTest > rendersBoard() FAILED")
        # Exclude the BUILD FAILED line itself
        failed_lines = re.findall(
            r"FAILED$| FAILED",
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
            r"FAILED$| FAILED",
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


# Self-register with the qa_compress registry
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("gradle", gradle_check)
