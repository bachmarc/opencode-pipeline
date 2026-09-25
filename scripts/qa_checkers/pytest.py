"""pytest checker plugin — self-registering checker for pytest test runs.

Runs pytest with --tb=short, extracts the summary line (regex: passed|failed|error|no tests),
and on failure extracts FAILED/ERROR lines for compact output.

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import re
import subprocess


def pytest_check() -> tuple[str, int]:
    """Run pytest and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    try:
        result = subprocess.run(
            ["pytest", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "pytest not found on PATH\n", 1
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
        failed_lines = re.findall(r"^(FAILED|ERROR) .*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without assertion details)
        short_lines = re.findall(r"^(FAILED|ERROR) .*$", output, re.MULTILINE)
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


# Self-register with the qa_compress registry
# Import at the end to ensure the function is defined first
import sys
from pathlib import Path

# Get the parent directory (scripts) to import qa_compress
script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("pytest", pytest_check)
