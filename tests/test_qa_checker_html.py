"""Tests for the HTML checker plugin (story 12-05).

Every test uses ``tmp_path`` as a fake project root with a ``qa_config.json``
and invokes the real ``scripts/qa_compress.py`` from there. The external-
system fake is the tmp_path project root itself; the checker validates files
via the stdlib ``html.parser`` (no extra dependency), so the real python3 runs
and no stub is needed.

Checker contract (simple syntax check, documented simplification):
- Void-tag whitelist (``br``, ``hr``, ``img``, ``input``, ``meta``, ``link``,
  ``area``, ``base``, ``col``, ``embed``, ``source``, ``track``, ``wbr``):
  opening tags need no closing.
- Every other open tag must be closed with a matching close tag in correct
  order (stack discipline).
- ``p`` is excluded from stack checking — implicit close is legal in HTML
  (documented simplification).

Exclusions (deterministic contract, no gitignore parsing): the walk skips
``.git``, ``.pipeline``, ``.worktrees``, ``node_modules``, ``__pycache__``,
``.pytest_cache``, ``dist`` and ``build``.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
QA_SCRIPT = REPO_ROOT / "scripts" / "qa_compress.py"


def _write_config(tmp_path: Path, checkers: list[str]) -> None:
    (tmp_path / "qa_config.json").write_text(
        '{"checkers": ' + repr(checkers).replace("'", '"') + "}",
        encoding="utf-8",
    )


def _run_qa_compress(cwd: Path) -> subprocess.CompletedProcess[str]:
    """Run the real qa_compress.py from the fake project root."""
    return subprocess.run(
        [sys.executable, str(QA_SCRIPT)],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
        timeout=60,
    )


def test_html_pass(tmp_path: Path) -> None:
    """Valid HTML (doctype, head/body, div) -> PASS, '1 files checked, 0 invalid'."""
    _write_config(tmp_path, ["html"])
    (tmp_path / "index.html").write_text(
        "<!DOCTYPE html><html><head></head><body><div>hi</div></body></html>",
        encoding="utf-8",
    )

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "## html (exit: 0)" in result.stdout
    assert "1 files checked, 0 invalid" in result.stdout
    assert "overall: PASS" in result.stdout
    assert "INVALID" not in result.stdout


def test_html_unclosed(tmp_path: Path) -> None:
    """Missing </div> -> FAIL, INVALID path with reason 'unclosed div'."""
    _write_config(tmp_path, ["html"])
    (tmp_path / "qa_config.json").write_text(
        '{"checkers": ["html"]}', encoding="utf-8"
    )
    (tmp_path / "broken.html").write_text(
        "<!DOCTYPE html><html><head></head><body><div>hi</body></html>",
        encoding="utf-8",
    )

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout
    assert "## failed_files" in result.stdout
    assert "INVALID broken.html (unclosed div)" in result.stdout
    assert "1 files checked, 1 invalid" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_html_mismatch(tmp_path: Path) -> None:
    """Wrong close tag (<div>text</span>) -> FAIL, reason contains 'mismatch'."""
    _write_config(tmp_path, ["html"])
    (tmp_path / "broken.html").write_text(
        "<!DOCTYPE html><html><head></head><body><div>text</span></body></html>",
        encoding="utf-8",
    )

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 1, result.stdout
    assert "## failed_files" in result.stdout
    assert "INVALID broken.html" in result.stdout
    assert "mismatch" in result.stdout
    assert "overall: FAIL" in result.stdout


def test_html_void_tags_ok(tmp_path: Path) -> None:
    """Void tags (br/img) and implicitly closed p -> PASS (no false positive)."""
    _write_config(tmp_path, ["html"])
    (tmp_path / "page.html").write_text(
        "<!DOCTYPE html><html><head></head><body><p>text<br><img src=\"x.png\">"
        "</body></html>",
        encoding="utf-8",
    )

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "1 files checked, 0 invalid" in result.stdout
    assert "INVALID" not in result.stdout
    assert "overall: PASS" in result.stdout


def test_html_excludes_dirs(tmp_path: Path) -> None:
    """Broken HTML inside node_modules/ is NOT walked -> checker still PASS."""
    _write_config(tmp_path, ["html"])
    nm = tmp_path / "node_modules" / "pkg"
    nm.mkdir(parents=True)
    (nm / "x.html").write_text("<div>never closed", encoding="utf-8")

    result = _run_qa_compress(tmp_path)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 files checked, 0 invalid" in result.stdout
    assert "INVALID" not in result.stdout
    assert "overall: PASS" in result.stdout