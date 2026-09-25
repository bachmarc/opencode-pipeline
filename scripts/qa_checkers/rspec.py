"""rspec checker plugin — self-registering checker for rspec test runs.

Runs rspec with --format progress, extracts the summary line (N examples, M failures),
and on failure extracts rspec ./spec/...rb:LINE # description lines.

Registers itself with the qa_compress registry at module import time.
"""

from __future__ import annotations

import re
import subprocess


def rspec_check() -> tuple[str, int]:
    """Run rspec and return compressed output with exit code.
    
    Returns:
        Tuple of (compressed_output: str, exit_code: int).
    """
    try:
        result = subprocess.run(
            ["rspec", "--format", "progress"],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except FileNotFoundError:
        return "rspec not found on PATH\n", 1
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


# Self-register with the qa_compress registry
import sys
from pathlib import Path

script_dir = Path(__file__).resolve().parent.parent
if str(script_dir) not in sys.path:
    sys.path.insert(0, str(script_dir))

from qa_compress import register_check  # noqa: E402

register_check("rspec", rspec_check)
