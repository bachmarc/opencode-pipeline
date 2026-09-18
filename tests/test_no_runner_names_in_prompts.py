"""
Invariant: portable agent/command prompts contain NO concrete test-runner names.

Story 12-07 (polyglot-qa / F-008): runner names (pytest, rspec, jest, gradle,
maven) are a project-level decision and must not be hard-wired into the
framework's portable prompts. Prompts reference "the project's configured
test suite" / `qa_config.json` instead. Runner names live where they belong:
in the project's `qa_config.json` and in `scripts/qa_compress.sh` checker
implementations (which are NOT scanned here).

Allowlist policy: the framework itself REQUIRES naming a runner only outside
portable prompts (qa_compress.sh checker docs, requirements.txt pins). This
test intentionally starts with an EMPTY allowlist for agent/ and command/ —
add an entry only with an explicit story that justifies why a portable prompt
must name a specific runner.
"""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Forbidden runner names (case-insensitive substring match).
FORBIDDEN_RUNNERS = ("pytest", "rspec", "jest", "gradle", "maven")

# Allowlist: lines containing one of these markers are exempt from the
# runner-name scan. Kept per directory; empty means zero exemptions.
# NOT for portable prompts — documented escape hatch only.
ALLOWLIST: dict[str, tuple[str, ...]] = {
    "agent": (),  # no legitimate runner mentions in agent prompts
    "command": (),  # no legitimate runner mentions in command prompts
}


def _runner_violations(directory: str) -> list[str]:
    """Collect runner-name violations in <directory>/*.md (case-insensitive)."""
    base = REPO_ROOT / directory
    files = sorted(base.glob("*.md"))
    assert files, f"no {directory}/*.md files found"

    allowed = ALLOWLIST[directory]
    violations: list[str] = []
    for path in files:
        rel = path.relative_to(REPO_ROOT).as_posix()
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if any(marker in line for marker in allowed):
                continue
            lowered = line.lower()
            for runner in FORBIDDEN_RUNNERS:
                if runner in lowered:
                    violations.append(f"{rel}:{lineno}: {line.strip()[:100]}")
                    break
    return violations


def test_no_runner_names_in_agent_prompts() -> None:
    """Every agent/*.md: no occurrence of pytest/rspec/jest/gradle/maven (case-insensitive)."""
    violations = _runner_violations("agent")
    assert not violations, (
        "runner names found in agent prompts — genericize to "
        "'the project's configured test suite' / qa_config.json:\n"
        + "\n".join(violations)
    )


def test_no_runner_names_in_command_prompts() -> None:
    """Every command/*.md: no occurrence of pytest/rspec/jest/gradle/maven (case-insensitive)."""
    violations = _runner_violations("command")
    assert not violations, (
        "runner names found in command prompts — genericize to "
        "'the project's configured test suite' / configured checkers:\n"
        + "\n".join(violations)
    )


def test_generic_testsuite_wording_present() -> None:
    """Prompts use the generic 'configured test suite' wording (semantics unchanged)."""
    architect = (REPO_ROOT / "agent" / "architect.md").read_text(encoding="utf-8")
    assert "Do NOT run the test suite yourself" in architect, (
        "architect.md missing 'Do NOT run the test suite yourself' rule"
    )

    qa_manager = (REPO_ROOT / "agent" / "qa-manager.md").read_text(encoding="utf-8")
    assert (
        "configured test suite" in qa_manager or "configured checkers" in qa_manager
    ), "qa-manager.md missing 'configured test suite' / 'configured checkers' wording"

    developer = (REPO_ROOT / "agent" / "developer.md").read_text(encoding="utf-8")
    assert "configured test suite" in developer, (
        "developer.md missing 'configured test suite' wording"
    )