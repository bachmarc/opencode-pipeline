"""Worktree cleanup script tests (Story 32-03).

Tests for scripts/worktree_cleanup.py — classification of git-registered
worktrees (merged / unmerged / dirty), safe removal of merged-and-clean
worktrees only, and the 29-01 R1.5 purge contract for orphan folders.
Also covers the staleness summary line in scripts/session_recovery.py.

Fixture repos are real git repositories with linked worktrees inside
pytest tmp_path; no external systems required.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Make repo root importable for scripts
REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

MERGED_WT = "30-01-merged"
UNMERGED_WT = "30-02-unmerged"
DIRTY_WT = "30-03-dirty"
INERT_ORPHAN = "30-04-inert"
DEAD_LINK_ORPHAN = "30-05-deadlink"


def run_cleanup_script(args: list[str], cwd: Path) -> tuple[int, str, str]:
    """Run worktree_cleanup.py with given args in the given repo directory.

    Returns: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, str(SCRIPTS_DIR / "worktree_cleanup.py")] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def run_session_recovery_script(
    args: list[str], cwd: Path
) -> tuple[int, str, str]:
    """Run session_recovery.py with given args in the given repo directory.

    Returns: (exit_code, stdout, stderr)
    """
    cmd = [sys.executable, str(SCRIPTS_DIR / "session_recovery.py")] + args
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(cwd),
        check=False,
    )
    return result.returncode, result.stdout, result.stderr


def git(path: Path, *args: str) -> str:
    """Run a git command, assert success, return stripped stdout."""
    result = subprocess.run(
        ["git", *args],
        cwd=str(path),
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, f"git {' '.join(args)} failed: {result.stderr}"
    return result.stdout.strip()


def init_git_repo(repo_path: Path) -> None:
    """Initialize a git repository with one commit on branch main."""
    repo_path.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["git", "init"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    (repo_path / "README.md").write_text("base\n")
    subprocess.run(
        ["git", "add", "-A"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "branch", "-M", "main"],
        cwd=str(repo_path),
        capture_output=True,
        check=True,
    )


@pytest.fixture
def fixture_repo(tmp_path: Path) -> Path:
    """Repo with three linked worktrees plus two orphan folders.

    - 30-01-merged:   branch at main's commit (merged), clean worktree
    - 30-02-unmerged: branch one commit ahead of main, clean worktree
    - 30-03-dirty:    branch at main's commit, uncommitted change
    - 30-04-inert:    orphan folder WITHOUT .git link (purgeable)
    - 30-05-deadlink: orphan folder WITH dead .git link (report only)
    """
    repo = tmp_path / "repo"
    init_git_repo(repo)

    # merged + clean: branch created at main's commit
    git(repo, "worktree", "add", f".worktrees/{MERGED_WT}", "-b", f"feature/{MERGED_WT}")

    # unmerged: one commit ahead of main
    git(repo, "worktree", "add", f".worktrees/{UNMERGED_WT}", "-b", f"feature/{UNMERGED_WT}")
    unmerged_path = repo / ".worktrees" / UNMERGED_WT
    (unmerged_path / "wip.txt").write_text("wip\n")
    git(unmerged_path, "add", "-A")
    git(unmerged_path, "commit", "-m", "wip")

    # dirty: branch at main's commit, uncommitted change in worktree
    git(repo, "worktree", "add", f".worktrees/{DIRTY_WT}", "-b", f"feature/{DIRTY_WT}")
    (repo / ".worktrees" / DIRTY_WT / "dirty.txt").write_text("uncommitted\n")

    # inert orphan folder (no .git link) — an inert remnant
    inert = repo / ".worktrees" / INERT_ORPHAN
    inert.mkdir()
    (inert / "leftover.txt").write_text("remnant\n")

    # orphan folder with a DEAD .git link (points to a missing gitdir)
    dead = repo / ".worktrees" / DEAD_LINK_ORPHAN
    dead.mkdir()
    (dead / ".git").write_text(
        "gitdir: /nonexistent/definitely-missing/worktrees/dead\n"
    )

    return repo


def test_list_classifies_merged_unmerged_dirty(fixture_repo: Path) -> None:
    """list mode classifies registered worktrees merged/unmerged/dirty."""
    exit_code, stdout, stderr = run_cleanup_script(["list"], fixture_repo)

    assert exit_code == 0, f"list failed: {stderr}"
    plan = json.loads(stdout)

    by_name = {Path(w["path"]).name: w for w in plan["worktrees"]}
    assert by_name[MERGED_WT]["classification"] == "merged"
    assert by_name[MERGED_WT]["branch"] == f"feature/{MERGED_WT}"
    assert by_name[MERGED_WT]["action"] == "remove"

    assert by_name[UNMERGED_WT]["classification"] == "unmerged"
    assert by_name[UNMERGED_WT]["action"] == "keep"

    assert by_name[DIRTY_WT]["classification"] == "dirty"
    assert by_name[DIRTY_WT]["action"] == "keep"

    # both orphan folders counted (not registered with git)
    assert plan["orphan_folders"] == 2


def test_apply_removes_merged_clean_only(fixture_repo: Path) -> None:
    """--apply removes the merged+clean worktree AND deletes its branch;
    unmerged and dirty worktrees survive untouched."""
    exit_code, stdout, stderr = run_cleanup_script(["--apply"], fixture_repo)

    assert exit_code == 0, f"apply failed: {stderr}"
    output = json.loads(stdout)

    removed_names = [Path(r["path"]).name for r in output["removed"]]
    assert MERGED_WT in removed_names
    removed_branches = [r["branch"] for r in output["removed"]]
    assert f"feature/{MERGED_WT}" in removed_branches

    # merged worktree directory gone, branch deleted
    assert not (fixture_repo / ".worktrees" / MERGED_WT).exists()
    assert git(fixture_repo, "branch", "--list", f"feature/{MERGED_WT}") == ""

    # unmerged and dirty worktrees survive untouched
    assert (fixture_repo / ".worktrees" / UNMERGED_WT).exists()
    assert (fixture_repo / ".worktrees" / DIRTY_WT).exists()

    # orphan folders are NOT touched without --purge-folders
    assert (fixture_repo / ".worktrees" / INERT_ORPHAN).exists()


def test_apply_refuses_unmerged_branch_delete(fixture_repo: Path) -> None:
    """--apply never deletes unmerged branches (safe delete contract)."""
    exit_code, stdout, stderr = run_cleanup_script(["--apply"], fixture_repo)

    assert exit_code == 0, f"apply failed: {stderr}"

    # unmerged branch still resolvable (git branch -d would refuse it too)
    assert git(
        fixture_repo, "rev-parse", "--verify", "--quiet",
        f"refs/heads/feature/{UNMERGED_WT}",
    )
    # dirty worktree's branch still exists as well
    assert git(
        fixture_repo, "rev-parse", "--verify", "--quiet",
        f"refs/heads/feature/{DIRTY_WT}",
    )


def test_purge_folders_orphans_only(fixture_repo: Path) -> None:
    """--purge-folders deletes only the inert orphan folder; requires --apply."""
    # Contract (29-01 R1.5): purge WITHOUT --apply is refused, deletes nothing
    exit_code, _, _ = run_cleanup_script(["--purge-folders"], fixture_repo)
    assert exit_code != 0
    assert (fixture_repo / ".worktrees" / INERT_ORPHAN).exists()

    # With --apply the inert orphan folder is purged
    exit_code, stdout, stderr = run_cleanup_script(
        ["--apply", "--purge-folders"], fixture_repo
    )
    assert exit_code == 0, f"apply+purge failed: {stderr}"
    output = json.loads(stdout)

    purged = [Path(p).name for p in output["purged_folders"]]
    assert INERT_ORPHAN in purged
    assert not (fixture_repo / ".worktrees" / INERT_ORPHAN).exists()


def test_purge_folders_reports_dead_git_link(fixture_repo: Path) -> None:
    """A folder WITH a dead .git link is reported, never deleted."""
    exit_code, stdout, stderr = run_cleanup_script(
        ["--apply", "--purge-folders"], fixture_repo
    )

    assert exit_code == 0, f"apply+purge failed: {stderr}"
    output = json.loads(stdout)

    reported = [Path(r["path"]).name for r in output["reported_folders"]]
    assert DEAD_LINK_ORPHAN in reported
    # reported folder must still exist on disk
    assert (fixture_repo / ".worktrees" / DEAD_LINK_ORPHAN).exists()


def test_default_list_mutates_nothing(fixture_repo: Path) -> None:
    """Default call (list) is a pure dry-run: repo state identical before/after."""

    def snapshot() -> dict:
        return {
            "worktree_list": git(fixture_repo, "worktree", "list", "--porcelain"),
            "branches": git(fixture_repo, "branch", "--list"),
            "folders": sorted(
                p.name for p in (fixture_repo / ".worktrees").iterdir()
            ),
            "files": sorted(
                str(p.relative_to(fixture_repo))
                for p in fixture_repo.rglob("*")
                if p.is_file() and ".git" not in p.parts
            ),
        }

    before = snapshot()
    exit_code, stdout, stderr = run_cleanup_script([], fixture_repo)

    assert exit_code == 0, f"list failed: {stderr}"
    json.loads(stdout)  # output must be a valid JSON plan
    assert snapshot() == before, "default list call mutated repo state"


def test_session_recovery_staleness_line(tmp_path: Path) -> None:
    """session_recovery prints the staleness line when merged worktrees exist,
    and no staleness line when none exist."""
    # Repo WITH a merged worktree -> staleness line expected
    repo = tmp_path / "repo_with_merged"
    init_git_repo(repo)
    (repo / ".pipeline").mkdir()
    (repo / ".pipeline" / "intent.json").write_text('{"intents": []}')
    git(repo, "worktree", "add", f".worktrees/{MERGED_WT}", "-b", f"feature/{MERGED_WT}")

    exit_code, _, stderr = run_session_recovery_script([], repo)
    assert exit_code == 0, f"session_recovery failed"
    staleness_lines = [line for line in stderr.splitlines() if "Staleness" in line]
    assert len(staleness_lines) == 1, f"expected exactly one staleness line in: {stderr}"
    assert "1" in staleness_lines[0]
    assert "worktree_cleanup" in staleness_lines[0]

    # Repo with an UNMERGED worktree only -> no staleness line
    repo2 = tmp_path / "repo_unmerged_only"
    init_git_repo(repo2)
    (repo2 / ".pipeline").mkdir()
    (repo2 / ".pipeline" / "intent.json").write_text('{"intents": []}')
    git(repo2, "worktree", "add", f".worktrees/{UNMERGED_WT}", "-b", f"feature/{UNMERGED_WT}")
    unmerged_path = repo2 / ".worktrees" / UNMERGED_WT
    (unmerged_path / "wip.txt").write_text("wip\n")
    git(unmerged_path, "add", "-A")
    git(unmerged_path, "commit", "-m", "wip")

    exit_code, _, stderr2 = run_session_recovery_script([], repo2)
    assert exit_code == 0
    assert not any("Staleness" in line for line in stderr2.splitlines()), (
        f"unexpected staleness line in: {stderr2}"
    )
