"""maven checker plugin — self-registering checker for maven test runs.

Runs mvn test, extracts the "Tests run: N, Failures: M, ..." summary,
and on failure extracts [ERROR] and FAILURE! lines.

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import re
import subprocess


def maven_check() -> tuple[str, int]:
    """Run mvn test and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    try:
        result = subprocess.run(
            ["mvn", "test"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "mvn not found on PATH\n", 1
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
        failed_lines = re.findall(r"<<< FAILURE!.*$", output, re.MULTILINE)
        if failed_lines:
            compressed += "## failed_tests\n"
            for line in failed_lines[-20:]:  # Last 20
                compressed += line + "\n"
        
        # Extract short test summary (without details)
        short_lines = re.findall(r"<<< FAILURE!.*$", output, re.MULTILINE)
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

register_check("maven", maven_check)
