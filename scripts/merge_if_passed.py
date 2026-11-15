#!/usr/bin/env python3
"""Merge validation script.

Checks .pipeline/qa-state/ for QA-PASS verdict and documenter-reconcile commit before merging.

Usage:
  merge_if_passed.py <branch>

Behavior:
- Extracts story-id from branch name (e.g., feature/06-11-qa-scripts → 06-11)
- Checks .pipeline/qa-state/<story-id>.json for PASS verdict
- Checks for at least one commit with message starting with "docs: reconcile" on the branch
- If both checks pass: git merge --no-ff <branch> into current branch
- Post-merge main health (Story 32-02): after a successful merge the
  CONFIGURED suite runs on the merged main checkout. The suite is whatever
  ``qa_config.json`` in the repo root configures, executed via the QA gate
  script ``scripts/qa_compress.py`` (same checker selection the pre-merge
  gate uses — no hardcoded runner here):
  * suite green       -> output gains ``"post_merge": {"suite": "PASS"}`` (exit 0)
  * suite FAIL        -> ``"post_merge": {"suite": "FAIL", "note": ...}`` and
    NEW exit code 3. NO rollback — the merge commit stays (rollback would
    destroy the merge-commit trail); the follow-up is a fix story created
    immediately (30-06 pattern), and no further stories are merged onto red main.
  * runners unavailable (e.g. a configured checker's binary is missing, the
    suite script itself is absent) -> ``"post_merge": {"suite": "SKIPPED",
    "reason": ...}`` exit 0 (fail-open — missing tooling must not block merges
    nor fake a red main).
- Story file status update (Story 33-01): after a successful merge,
  ``merge_if_passed.py`` updates the story file's ``Status:`` line to
  ``Status: Done (merged as <short-sha>)`` where ``<short-sha>`` is the
  7-char merge commit SHA. If the story file cannot be found or the
  ``Status:`` line is missing, the merge still succeeds but a warning is
  printed. The cleanup hint for worktree removal is also printed.
- If no PASS: exit code 1 + error JSON
- If no documenter commit: exit code 1 + error JSON
- On merge conflict: exit code 2

Output: JSON to stdout
  Success: {"merged": true, "branch": "...", "commit": "...", "post_merge": {...}}
  No PASS: {"error": "Merge blocked: no QA-PASS for ..."}
  No documenter: {"error": "Merge blocked: documenter not run on ..."}
  Conflict: {"error": "Merge conflict on branch ..."}

Exit codes:
  0 - Merged successfully (post-merge suite PASS or SKIPPED)
  1 - No QA-PASS record found, no documenter commit, or merge failed
  2 - Merge conflict
  3 - Merged, but the post-merge suite FAILED on main (no rollback)
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

# Fixed note text for a red post-merge suite (Story 32-02 contract).
_POST_MERGE_FAIL_NOTE = (
    "main is red — create a fix story immediately (30-06 pattern); "
    "do NOT merge further stories onto red main"
)

# Runner-availability probe for the post-merge suite (Story 32-02): maps a
# configured checker name to the binaries it requires (ANY one of them
# suffices; mirrors the runner lookups inside scripts/qa_compress.py). An
# empty tuple needs no external binary (stdlib / python-module checkers).
# This map decides only PASS/FAIL vs SKIPPED — the SUITE itself is whatever
# qa_config.json configures (no hardcoded runner); when the probe cannot
# vouch for a checker's tooling the suite is skipped (fail-open), never
# faked into a red main. Unknown checker names are not probed: the suite
# fails loudly on them, exactly like the QA gate does.
_CHECKER_RUNNERS: dict[str, tuple[str, ...]] = {
    "pytest": ("pytest",),
    "rspec": ("rspec",),
    "jest": ("jest",),
    "eslint": ("eslint",),
    "tsc": ("tsc",),
    "prettier": ("prettier",),
    "npm-audit": ("npm",),
    "gradle": ("gradle",),
    "maven": ("mvn",),
    "json": (),
    "yaml": (),  # python module — probed via importlib (see _missing_runners)
    "html": (),
    "rubocop": ("rubocop",),  # bundle-only setups are skipped (fail-open)
    "checkstyle": ("gradlew", "mvn", "checkstyle"),
    "mypy": ("mypy",),
    "ruff": ("ruff",),
    "black": ("black",),
    "worktree_discipline": ("git",),
    "metadata_affects": ("git",),
}


def get_repo_root() -> Path:
    """Find repo root by looking for .git directory."""
    current = Path.cwd()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    return Path.cwd()


def extract_story_id(branch: str) -> str | None:
    """Extract story ID from branch name.
    
    Examples:
    - feature/06-11-qa-scripts → 06-11
    - feature/06-05-test → 06-05
    """
    # Match pattern: feature/<digits>-<digits>-...
    match = re.match(r"feature/(\d+-\d+)", branch)
    if match:
        return match.group(1)
    return None


def check_qa_pass(story_id: str) -> bool:
    """Check if story has QA-PASS verdict."""
    repo_root = get_repo_root()
    state_file = repo_root / ".pipeline" / "qa-state" / f"{story_id}.json"
    
    if not state_file.exists():
        return False
    
    try:
        data = json.loads(state_file.read_text())
        verdicts = data.get("verdicts", [])
        
        # Check if last verdict is PASS
        return bool(verdicts and verdicts[-1].get("verdict") == "PASS")
    except Exception:  # noqa: BLE001
        return False


def check_documenter_commit(branch: str) -> bool:
    """Check if branch has at least one commit with message starting with 'docs: reconcile'.
    
    Uses: git log main..<branch> --oneline --grep="^docs: reconcile"
    Scopes the check to branch-exclusive commits only (commits on branch but not on main).
    Returns True if at least one matching commit found, False otherwise.
    """
    result = subprocess.run(
        ["git", "log", f"main..{branch}", "--oneline", "--grep=^docs: reconcile"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    # If returncode is 0 and there's output, we found matching commits
    return result.returncode == 0 and bool(result.stdout.strip())


def get_current_branch() -> str | None:
    """Get current git branch name."""
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def get_commit_hash(branch: str) -> str | None:
    """Get commit hash for a branch."""
    result = subprocess.run(
        ["git", "rev-parse", branch],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return None


def _update_story_status(story_file: Path, sha: str) -> bool:
    """Update the Status: line in a story file to Done (merged as <sha>).
    
    Rewrites the Status: line (or warns if not found). The short SHA is typically
    7 characters (git abbreviation).
    
    Args:
        story_file: Path to the story file (e.g., docs/features/F-033/stories/33-01-*.md)
        sha: Merge commit SHA (typically 7-char abbreviated)
    
    Returns:
        True if update succeeded, False if story file not found or Status line not found.
    """
    if not story_file.exists():
        print(f"WARNING: could not update status in {story_file}: file not found", file=sys.stderr)
        return False
    
    try:
        content = story_file.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"WARNING: could not update status in {story_file}: read error", file=sys.stderr)
        return False
    
    # Find and replace the Status: line
    lines = content.split("\n")
    updated = False
    for i, line in enumerate(lines):
        if line.startswith("Status:"):
            lines[i] = f"Status: Done (merged as {sha})"
            updated = True
            break
    
    if not updated:
        print(f"WARNING: could not update status in {story_file}: Status line not found", file=sys.stderr)
        return False
    
    try:
        story_file.write_text("\n".join(lines), encoding="utf-8")
        return True
    except (OSError, UnicodeEncodeError):
        print(f"WARNING: could not update status in {story_file}: write error", file=sys.stderr)
        return False


def _find_story_file(story_id: str, repo_root: Path | None = None) -> Path | None:
    """Find story file using glob pattern.
    
    Looks for docs/features/*/stories/<story-id>-*.md in the repo root.
    
    Args:
        story_id: Story ID (e.g., "33-01")
        repo_root: Repo root path (if None, uses get_repo_root())
    
    Returns:
        Path to story file if found, None otherwise.
    """
    root = repo_root if repo_root is not None else get_repo_root()
    
    # Use glob to find matching files
    matches = list(root.glob(f"docs/features/*/stories/{story_id}-*.md"))
    
    if matches:
        return matches[0]  # Return first match
    return None


def merge_branch(branch: str) -> tuple[bool, str | None]:
    """Merge branch with --no-ff flag.

    Returns: (success, commit_hash or error_message)
    """
    result = subprocess.run(
        ["git", "merge", "--no-ff", branch, "-m", f"Merge {branch}"],
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode == 0:
        # Get the merge commit hash
        commit_hash = get_commit_hash("HEAD")
        return True, commit_hash

    # Check if it's a merge conflict
    if "conflict" in result.stderr.lower() or "conflict" in result.stdout.lower():
        return False, "Merge conflict"

    return False, result.stderr or result.stdout


def _configured_checkers(repo_root: Path) -> list[str] | None:
    """Configured checker names from qa_config.json in the repo root.

    Same selection logic as the QA gate (scripts/qa_compress.py): a missing
    config file defaults to ``["pytest"]``. Returns None when the config
    exists but is unreadable or invalid — the suite could not determine its
    checkers, so the post-merge check reports SKIPPED (fail-open).
    """
    config_file = repo_root / "qa_config.json"
    if not config_file.exists():
        return ["pytest"]
    try:
        data = json.loads(config_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError):
        return None
    if (
        not isinstance(data, dict)
        or not isinstance(data.get("checkers"), list)
        or not all(isinstance(name, str) for name in data["checkers"])
    ):
        return None
    return list(data["checkers"])


def _missing_runners(checkers: list[str]) -> list[str]:
    """Configured checkers whose runner tooling is not available.

    Returns one ``"<checker> (<required binaries>)"`` string per unavailable
    checker (empty list when everything can run). The ``yaml`` checker needs
    the PyYAML python module instead of a binary and is probed via
    importlib. Unknown checker names are not probed — the suite itself fails
    loudly on them, mirroring the QA gate.
    """
    missing: list[str] = []
    for name in checkers:
        if name == "yaml":
            if importlib.util.find_spec("yaml") is None:
                missing.append("yaml (PyYAML module)")
            continue
        binaries = _CHECKER_RUNNERS.get(name)
        if not binaries:
            continue
        if not any(shutil.which(binary) for binary in binaries):
            missing.append(f"{name} ({', '.join(binaries)})")
    return missing


def run_post_merge_suite(repo_root: Path | None = None) -> dict:
    """Run the configured QA suite on the merged main checkout (Story 32-02).

    The suite is whatever ``qa_config.json`` in the repo root configures,
    executed via ``scripts/qa_compress.py`` (the same checker selection the
    pre-merge QA gate uses — no hardcoded runner). The repo root is the
    merged main checkout: cwd for the suite AND the source of the config.

    Returns:
        {"suite": "PASS"} — suite green (qa_compress exit 0).
        {"suite": "FAIL", "note": ...} — suite red; caller exits 3 and does
            NOT roll back the merge (the fix is a story, not a revert).
        {"suite": "SKIPPED", "reason": ...} — suite could not run (config
            unreadable, runner binary/module missing, suite script absent,
            interpreter unavailable): fail-open, one-line reason.
    """
    root = repo_root if repo_root is not None else get_repo_root()

    checkers = _configured_checkers(root)
    if checkers is None:
        return {
            "suite": "SKIPPED",
            "reason": "qa_config.json unreadable/invalid — configured suite unknown",
        }

    missing = _missing_runners(checkers)
    if missing:
        return {
            "suite": "SKIPPED",
            "reason": f"suite runner(s) unavailable: {'; '.join(missing)}",
        }

    suite_script = root / "scripts" / "qa_compress.py"
    if not suite_script.is_file():
        return {"suite": "SKIPPED", "reason": f"QA suite script not found: {suite_script}"}

    try:
        result = subprocess.run(
            [sys.executable, str(suite_script)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError:
        return {
            "suite": "SKIPPED",
            "reason": "QA suite could not be started (python interpreter unavailable)",
        }

    if result.returncode == 0:
        return {"suite": "PASS"}
    return {"suite": "FAIL", "note": _POST_MERGE_FAIL_NOTE}


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Merge validation script"
    )
    parser.add_argument("branch", help="Branch to merge (e.g., feature/06-11-qa-scripts)")
    
    args = parser.parse_args()
    branch = args.branch
    
    # Extract story ID from branch name
    story_id = extract_story_id(branch)
    if not story_id:
        output = {
            "error": f"Could not extract story ID from branch name: {branch}",
        }
        print(json.dumps(output))
        return 1
    
    # Check for QA-PASS verdict
    if not check_qa_pass(story_id):
        output = {
            "error": f"Merge blocked: no QA-PASS for {branch}",
        }
        print(json.dumps(output))
        return 1
    
    # Check for documenter-reconcile commit
    if not check_documenter_commit(branch):
        output = {
            "error": f"Merge blocked: documenter not run on {branch}. Run /document first.",
        }
        print(json.dumps(output))
        return 1
    
    # Attempt merge
    success, result = merge_branch(branch)

    if success:
        # Post-merge main health (Story 32-02): run the configured suite on
        # the merged main. NO rollback on FAIL — the merge commit stays; the
        # follow-up is a fix story (30-06 pattern), surfaced via exit code 3.
        post_merge = run_post_merge_suite()
        
        # Story 33-01: Update story file Status line
        short_sha = result[:7] if result and len(result) >= 7 else result
        story_id = extract_story_id(branch)
        if story_id:
            story_file = _find_story_file(story_id)
            if story_file:
                _update_story_status(story_file, short_sha)
            else:
                print(f"WARNING: could not find story file for {story_id}", file=sys.stderr)
        
        output = {
            "merged": True,
            "branch": branch,
            "commit": result,
            "post_merge": post_merge,
        }
        print(json.dumps(output))
        print("Hint: run 'python scripts/worktree_cleanup.py --apply' to remove the merged worktree.", file=sys.stderr)
        
        return 3 if post_merge.get("suite") == "FAIL" else 0
    
    # Merge failed
    if "conflict" in result.lower():
        output = {
            "error": f"Merge conflict on branch {branch}",
        }
        print(json.dumps(output))
        return 2
    
    output = {
        "error": f"Merge failed: {result}",
    }
    print(json.dumps(output))
    return 1


if __name__ == "__main__":
    sys.exit(main())
