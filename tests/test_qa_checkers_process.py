"""Tests for the Tier D process checkers (story 30-03).

Covers the two registry checkers in ``scripts/qa_compress.py`` that inspect
git state instead of running a tool binary:

- ``worktree_discipline`` — the story worktree must be registered under
  ``<worktree_root>/<story-id>-*`` with the story branch checked out in it.
  The story id comes from the CURRENT git branch
  (``feature/<story-id>-<slug>``); ``qa_config.json``
  ``process_checker.story_id`` is a fallback override for out-of-worktree
  runs.
- ``metadata_affects`` — commit metadata consistency across ALL branch
  commits since the merge base with the default branch (not just the last
  commit): every ``affects:`` path must exist in the repo, and every changed
  ``src/``/``tests/`` file must be declared in some commit's
  ``symbols:``/``affects:`` values (docs/planning-only branches pass without
  declarations).

Unlike the tool checkers (stub runner binaries), these tests build REAL
temporary git repositories via subprocess ``git`` (``git init``, commits,
branches, worktrees — git is available in the test environment) and invoke
the real ``scripts/qa_compress.py`` from the fixture repo or story worktree.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


# ============================================================================
# Fixture helpers: real temporary git repositories
# ============================================================================

def _git(repo: Path, *args: str) -> subprocess.CompletedProcess[str]:
    """Run a git command inside ``repo`` and return the completed process."""
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=30,
    )


def _init_repo(tmp_path: Path) -> Path:
    """Create a real temp git repo with one initial commit on 'main'."""
    repo = tmp_path / "repo"
    repo.mkdir()
    init = _git(repo, "init", "-b", "main")
    assert init.returncode == 0, init.stderr
    assert _git(repo, "config", "user.name", "QA Fixture").returncode == 0
    assert _git(repo, "config", "user.email", "qa-fixture@example.invalid").returncode == 0
    (repo / "README.md").write_text("init\n", encoding="utf-8")
    assert _git(repo, "add", ".").returncode == 0
    commit = _git(repo, "commit", "-m", "initial commit")
    assert commit.returncode == 0, commit.stderr
    return repo


def _commit_file(repo: Path, rel_path: str, content: str, message: str) -> None:
    """Create/modify ``rel_path`` in the fixture repo and commit it."""
    target = repo / rel_path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    assert _git(repo, "add", rel_path).returncode == 0
    commit = _git(repo, "commit", "-m", message)
    assert commit.returncode == 0, commit.stderr


def _add_worktree(repo: Path, path: Path, branch: str) -> Path:
    """Register a git worktree at ``path`` checking out ``branch``."""
    result = _git(repo, "worktree", "add", str(path), branch)
    assert result.returncode == 0, result.stderr
    return path if path.is_absolute() else repo / path


def _run_qa_compress(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real qa_compress.py from ``cwd`` (the QA-checked project root)."""
    return subprocess.run(
        [sys.executable, str(QA_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
        timeout=60,
    )


def _write_config(cwd: Path, content: str) -> None:
    (cwd / "qa_config.json").write_text(content, encoding="utf-8")


# ============================================================================
# worktree_discipline tests
# ============================================================================

def test_worktree_discipline_pass(tmp_path: Path) -> None:
    """Story branch exists, worktree registered under .worktrees/<id>-* -> exit 0."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "branch", "feature/30-03-x").returncode == 0
    _add_worktree(repo, repo / ".worktrees" / "30-03-x", "feature/30-03-x")
    # Run from the main checkout (on 'main'): the story id comes from the
    # process_checker.story_id fallback override.
    _write_config(
        repo,
        '{"checkers": ["worktree_discipline"], '
        '"process_checker": {"story_id": "30-03"}}',
    )
    result = _run_qa_compress(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## worktree_discipline (exit: 0)" in result.stdout
    assert '"result": "PASS"' in result.stdout
    assert "feature/30-03-x" in result.stdout
    assert "30-03-x" in result.stdout  # worktree path in PASS payload
    assert "overall: PASS" in result.stdout


def test_worktree_discipline_stale(tmp_path: Path) -> None:
    """Branch exists but NO worktree registered -> exit 1, message mentions worktree."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "branch", "feature/30-03-x").returncode == 0
    _write_config(
        repo,
        '{"checkers": ["worktree_discipline"], '
        '"process_checker": {"story_id": "30-03"}}',
    )
    result = _run_qa_compress(repo)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## worktree_discipline (exit: 1)" in result.stdout
    assert "worktree" in result.stdout.lower()
    assert "overall: FAIL" in result.stdout


def test_worktree_discipline_wrong_dir(tmp_path: Path) -> None:
    """Worktree registered under an unexpected path (not .worktrees/<id>-*) -> exit 1."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "branch", "feature/30-03-x").returncode == 0
    elsewhere = _add_worktree(repo, tmp_path / "elsewhere" / "30-03-x", "feature/30-03-x")
    # Run from the (wrong) worktree: story id derived from the branch.
    _write_config(elsewhere, '{"checkers": ["worktree_discipline"]}')
    result = _run_qa_compress(elsewhere)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## worktree_discipline (exit: 1)" in result.stdout
    assert '"result": "FAIL"' in result.stdout
    assert "overall: FAIL" in result.stdout


def test_worktree_discipline_branch_in_main_checkout(tmp_path: Path) -> None:
    """Story branch checked out in the MAIN worktree, none under .worktrees -> exit 1.

    The real audit case (2026-10-30): the developer worked outside the story
    worktree, so the branch is checked out in the main checkout instead of a
    registered .worktrees/<id>-* worktree. The FAIL reason must name the
    worktree-root expectation.
    """
    repo = _init_repo(tmp_path)
    assert _git(repo, "branch", "feature/30-03-x").returncode == 0
    assert _git(repo, "checkout", "feature/30-03-x").returncode == 0
    _write_config(repo, '{"checkers": ["worktree_discipline"]}')
    result = _run_qa_compress(repo)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## worktree_discipline (exit: 1)" in result.stdout
    # FAIL reason names the worktree-root expectation (.worktrees/<id>-*)
    assert ".worktrees" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_worktree_story_id_from_branch(tmp_path: Path) -> None:
    """No process_checker.story_id config -> story id derived from the branch."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "branch", "feature/30-03-x").returncode == 0
    worktree = _add_worktree(repo, repo / ".worktrees" / "30-03-x", "feature/30-03-x")
    # Run from INSIDE the story worktree (the real QA location), config has
    # no story_id — the current branch feature/30-03-x provides it.
    _write_config(worktree, '{"checkers": ["worktree_discipline"]}')
    result = _run_qa_compress(worktree)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## worktree_discipline (exit: 0)" in result.stdout
    assert '"result": "PASS"' in result.stdout
    assert "overall: PASS" in result.stdout


# ============================================================================
# metadata_affects tests
# ============================================================================

def test_metadata_pass(tmp_path: Path) -> None:
    """Well-formed metadata (symbols/affects match the diff) -> exit 0."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "checkout", "-b", "feature/30-03-x").returncode == 0
    _commit_file(
        repo,
        "src/foo.py",
        "def foo() -> int:\n    return 1\n",
        "add foo\n\n"
        "symbols: foo | breaks: none | affects: src/foo.py | tests: 1 passed",
    )
    _write_config(repo, '{"checkers": ["metadata_affects"]}')
    result = _run_qa_compress(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## metadata_affects (exit: 0)" in result.stdout
    assert '"result": "PASS"' in result.stdout
    assert "overall: PASS" in result.stdout


def test_metadata_missing_affects(tmp_path: Path) -> None:
    """Code change without affects/symbols declaration -> exit 1, path listed."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "checkout", "-b", "feature/30-03-x").returncode == 0
    _commit_file(
        repo,
        "src/foo.py",
        "def foo() -> int:\n    return 1\n",
        "add foo\n\n"
        "symbols: foo | breaks: none | affects: nothing | tests: 1 passed",
    )
    _write_config(repo, '{"checkers": ["metadata_affects"]}')
    result = _run_qa_compress(repo)

    assert result.returncode == 1, result.stdout + result.stderr
    assert "## metadata_affects (exit: 1)" in result.stdout
    assert "src/foo.py" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_metadata_docs_only_commit(tmp_path: Path) -> None:
    """Docs commit changes no code paths -> PASS without declarations."""
    repo = _init_repo(tmp_path)
    assert _git(repo, "checkout", "-b", "feature/30-03-x").returncode == 0
    _commit_file(repo, "docs/plan.md", "# plan\n", "docs: planning")
    _write_config(repo, '{"checkers": ["metadata_affects"]}')
    result = _run_qa_compress(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## metadata_affects (exit: 0)" in result.stdout
    assert '"result": "PASS"' in result.stdout
    assert "overall: PASS" in result.stdout


def test_metadata_multi_commit_scope(tmp_path: Path) -> None:
    """Only the LAST commit declares the paths -> still PASS (scope = whole branch).

    The branch has two commits since the merge base: the first changes
    src/foo.py without any metadata, the second declares both changed paths.
    Scope is the whole branch since the merge base, not the last commit.
    """
    repo = _init_repo(tmp_path)
    assert _git(repo, "checkout", "-b", "feature/30-03-x").returncode == 0
    _commit_file(repo, "src/foo.py", "def foo() -> int:\n    return 1\n", "add foo")
    _commit_file(
        repo,
        "tests/test_foo.py",
        "def test_foo() -> None:\n    assert True\n",
        "add tests\n\n"
        "symbols: foo | breaks: none | affects: src/foo.py tests/test_foo.py | tests: 1 passed",
    )
    _write_config(repo, '{"checkers": ["metadata_affects"]}')
    result = _run_qa_compress(repo)

    assert result.returncode == 0, result.stdout + result.stderr
    assert '"result": "PASS"' in result.stdout
    assert "overall: PASS" in result.stdout


# ============================================================================
# config contract / registry selection tests
# ============================================================================

def test_not_selected_checkers_dont_run(tmp_path: Path) -> None:
    """Config with only ['pytest'] runs as before — process checkers stay OFF."""
    # No git repo needed: the pytest checker does not inspect git state.
    project = tmp_path / "project"
    project.mkdir()
    _write_config(project, '{"checkers": ["pytest"]}')
    result = _run_qa_compress(project)

    assert "## pytest" in result.stdout
    assert "## worktree_discipline" not in result.stdout
    assert "## metadata_affects" not in result.stdout


def test_process_checker_unknown_key_rejected(tmp_path: Path) -> None:
    """Unknown key inside the optional process_checker block -> validation error."""
    repo = _init_repo(tmp_path)
    _write_config(
        repo,
        '{"checkers": ["worktree_discipline"], '
        '"process_checker": {"bogus_key": "x"}}',
    )
    result = _run_qa_compress(repo)

    assert result.returncode == 1, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    assert "unknown process_checker key: bogus_key" in combined
    assert "Traceback" not in combined
