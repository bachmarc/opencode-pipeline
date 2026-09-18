"""Tests for check_template_constancy.py and check_architecture.py scripts."""

import json
import subprocess
import sys
from pathlib import Path


def test_scripts_exist():
    """Both scripts exist and compile."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    constancy_script = scripts_dir / "check_template_constancy.py"
    architecture_script = scripts_dir / "check_architecture.py"
    
    assert constancy_script.exists(), f"check_template_constancy.py not found at {constancy_script}"
    assert architecture_script.exists(), f"check_architecture.py not found at {architecture_script}"
    
    # Verify they compile
    result_constancy = subprocess.run(
        [sys.executable, "-m", "py_compile", str(constancy_script)],
        capture_output=True,
        text=True
    )
    assert result_constancy.returncode == 0, f"check_template_constancy.py compile error: {result_constancy.stderr}"
    
    result_architecture = subprocess.run(
        [sys.executable, "-m", "py_compile", str(architecture_script)],
        capture_output=True,
        text=True
    )
    assert result_architecture.returncode == 0, f"check_architecture.py compile error: {result_architecture.stderr}"


def test_template_constancy_pass(tmp_path):
    """Identical sections -> PASS."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    templates_dir = Path(__file__).parent.parent / "templates"
    
    # Read the actual template
    template_path = templates_dir / "AGENTS.md"
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Create a project AGENTS.md that is identical to the template
    test_agents = tmp_path / "AGENTS.md"
    test_agents.write_text(template_content, encoding='utf-8')
    
    # Run check_template_constancy.py
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "check_template_constancy.py"), str(test_agents)],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir.parent)
    )
    
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stdout: {result.stdout}. stderr: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["result"] == "PASS", f"Expected PASS, got {output}"


def test_template_constancy_fail(tmp_path):
    """Modified section -> FAIL with section name."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    # Create a project AGENTS.md with a modified constant section
    test_agents = tmp_path / "AGENTS.md"
    
    project_agents_content = """# AGENTS.md - Test Project

## This project: Test Project

- **What:** Test project
- **Stack:** Python
- **Versioning:** `APP_VERSION = "0.1.0"`

## Core rules

- Test rule 1
- Test rule 2

## Architecture: function vs connectivity

- Test architecture

## Git conventions

- Every story = its own branch: `feature/<story-id>-<slug>`.
- **Worktree discipline:** Developer sessions work in their own Git worktree
  `.worktrees/<story-id>-<slug>/` (created by architect). Main working dir stays on `main`.
- **No direct push to `main`.** Merge only after QA gate (PASS).
- Commit body carries metadata for QA requeue:
  ```
  symbols: <changed export symbols> | breaks: <none|breaking> | affects: <dependent files> | tests: <pytest result>
  ```

## Workflow

0. **Planning checkpoint (mandatory before every dev/QA start)** - for every requirement
   (new feature, replanning, bugfix, "small" change):
   1. **Planning phase (architect):** requirements/design/stories, REQ-IDs, doc updates.
   2. **Review checkpoint (user):** architect presents the concrete implementation overview -
      WHAT (stories + developer targets), HOW (waves, order, test criteria). **Dev+QA never
      start without explicit user-go** ("passt"/"go").
   3. **Then:** dev + QA per approved plan.
   - Applies to small changes and bugfix loops too - no implicit starts.
1. **Stories:** `STORIES.md` (index) + `docs/stories/<phase>-<id>-<slug>.md`. Every story links
   traceability (`REQ-XXX` + design section) and contains **test criteria that exist BEFORE
   implementation**.
2. **Developer:** implements EXACTLY the developer targets - nothing more, nothing less.
   Tests first, `pytest` green.
3. **QA gate:** checks requirements, tests, role abstraction, template constancy.
   PASS -> merge. FAIL -> fix loop (max 3), then BLOCKED -> back to architect/user.

## Languages

- Dialogue with user: respond in the user's language
- Code/identifiers: English
- Repo docs (README, requirements, design, stories): English
- Agent prompts: respond in the user's language

## Prohibitions

- No autonomous decomposition/implementation outside released stories.
- No unrequested features outside developer targets.
- No concrete model/provider names in portable files.
- No development in `~/.config/opencode` (live clone - pull only).
- MODIFIED LINE: No `git init`/writing outside the project path.

## References

- `docs/requirements.md` - source of truth for scope (REQ-IDs)
- `docs/design.md` - source of truth for architecture (two-clone, check design)
- `STORIES.md` - story index (status per story)
- `templates/AGENTS.md` - the skeleton every project fills in
"""
    
    test_agents.write_text(project_agents_content, encoding='utf-8')
    
    # Run check_template_constancy.py
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "check_template_constancy.py"), str(test_agents)],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir.parent)
    )
    
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
    
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL", f"Expected FAIL, got {output}"
    assert "sections" in output, f"Expected 'sections' key in output: {output}"
    assert "Prohibitions" in output["sections"], f"Expected 'Prohibitions' in sections: {output}"


def test_architecture_check_clean(tmp_path):
    """Stdlib-only imports -> PASS."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    # Create a test src/core directory with clean imports
    core_dir = tmp_path / "src" / "core"
    core_dir.mkdir(parents=True)
    
    clean_module = core_dir / "clean.py"
    clean_module.write_text("""
import sys
import os
from pathlib import Path
from typing import Dict, List

def process_data(data: Dict) -> List:
    return list(data.values())
""", encoding='utf-8')
    
    # Run check_architecture.py
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "check_architecture.py"), str(core_dir)],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir.parent)
    )
    
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["result"] == "PASS", f"Expected PASS, got {output}"
    assert "files_checked" in output, f"Expected 'files_checked' key in output: {output}"
    assert output["files_checked"] >= 1, f"Expected at least 1 file checked"


def test_architecture_check_violation(tmp_path):
    """Forbidden import -> FAIL with file/line."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    # Create a test src/core directory with forbidden imports
    core_dir = tmp_path / "src" / "core"
    core_dir.mkdir(parents=True)
    
    bad_module = core_dir / "bad.py"
    bad_module.write_text("""
import sys
import httpx

def fetch_data():
    return httpx.get("http://example.com")
""", encoding='utf-8')
    
    # Run check_architecture.py
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "check_architecture.py"), str(core_dir)],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir.parent)
    )
    
    assert result.returncode == 1, f"Expected exit 1, got {result.returncode}"
    
    output = json.loads(result.stdout)
    assert output["result"] == "FAIL", f"Expected FAIL, got {output}"
    assert "violations" in output, f"Expected 'violations' key in output: {output}"
    assert len(output["violations"]) > 0, f"Expected at least 1 violation"
    
    violation = output["violations"][0]
    assert "file" in violation, f"Expected 'file' in violation: {violation}"
    assert "import" in violation, f"Expected 'import' in violation: {violation}"
    assert "line" in violation, f"Expected 'line' in violation: {violation}"
    assert "httpx" in violation["import"], f"Expected 'httpx' in import: {violation}"


def test_architecture_check_allowlist(tmp_path):
    """Allowed import not flagged."""
    scripts_dir = Path(__file__).parent.parent / "scripts"
    
    # Create a test src/core directory with an import that would normally be forbidden
    core_dir = tmp_path / "src" / "core"
    core_dir.mkdir(parents=True)
    
    module_with_custom_import = core_dir / "custom.py"
    module_with_custom_import.write_text("""
import sys
import mylib

def process():
    return mylib.do_something()
""", encoding='utf-8')
    
    # Create an allowlist file
    allowlist_file = tmp_path / "allowlist.txt"
    allowlist_file.write_text("mylib\n", encoding='utf-8')
    
    # Run check_architecture.py with allowlist
    result = subprocess.run(
        [sys.executable, str(scripts_dir / "check_architecture.py"), str(core_dir), 
         "--allowlist", str(allowlist_file)],
        capture_output=True,
        text=True,
        cwd=str(scripts_dir.parent)
    )
    
    assert result.returncode == 0, f"Expected exit 0, got {result.returncode}. stderr: {result.stderr}"
    
    output = json.loads(result.stdout)
    assert output["result"] == "PASS", f"Expected PASS with allowlist, got {output}"
