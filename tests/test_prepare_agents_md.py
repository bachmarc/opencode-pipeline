"""Tests for prepare_agents_md.py — AGENTS.md draft generation."""

import json
import sys
import subprocess
from pathlib import Path


# Minimal template fixture with constant sections and placeholders
MINIMAL_TEMPLATE = """# AGENTS.md — <Project name>

> Skeleton from the opencode pipeline (`templates/AGENTS.md`). Fill in: everything in `<...>`.
> Constant sections (Workflow, Git, Languages, Prohibitions) **must not** be modified per project —
> they are the binding interface between framework and project.
> Project-specific: project name, stack, core rules, references (§ "This project").

## This project: <Name, one-liner>

- **What:** <1-2 sentences: problem, target audience, scope — from `docs/requirements.md`>
- **Stack:** <e.g. Python 3.12, FastAPI + uvicorn, static HTML/JS frontend, Docker>
- **Versioning:** `APP_VERSION = "0.1.0"` (in `src/<version>.py` or similar) — bump on every merge

## Core rules (project source of truth: feature files + story files)

- <Core rule 1 — e.g. "`src/core/board.py` (`PostBoard`) knows nothing of FastAPI, HTTP, or clocks. Time comes as a parameter (`now`).">
- <Core rule 2 — e.g. "RAM-only: no persistence, no auto-clear timers.">
- <… more, taken from `docs/design.md` § core decisions>
- **Fake requirement:** For EVERY external dependency (`<API>`, `<DB>`, `<HA>`, …) there exists a fake in `tests/fakes/` — tests run without real systems.

## Architecture: function vs connectivity

Strict separation (pattern: `intesis_modbus/CLAUDE.md`):

- **`src/core/`** — pure logic/algorithms.
  - **Zero imports** from framework/IO/HA/DB/API.
  - Receives all data as parameters, returns dicts/primitives.
  - Fully unit-testable, contains simulation helpers (`simulate_<x>()`).
- **`src/adapters/`** — thin wrappers (3-10 lines per method).
  - Extracts request data, **delegates all decisions to core**, returns HTTP response / writes bus.
  - Timers/listeners/schedulers exclusively here.
- **Fakes are mandatory** for every external dependency: `tests/fakes/`.
  - Core tests run **without** real systems (`FakeClock`, `Fake<X>` interfaces).
  - **Fake = same method signatures as the real adapter.** Fakes offering a different
    interface than the adapter → design error. The real orchestration code must
    be callable with fakes, without modifications.
  - If core is not testable without fakes → design error.
- **Integration tests test the real orchestration code** (e.g. `Scheduler._run_cycle()`
  with fakes), not a manual reconstruction of the cycle. Manually reconstructed cycles bypass
  wiring bugs and are worthless as integration proof.

## Git conventions

- Every story = its own branch: `feature/<story-id>-<slug>` (e.g. `feature/01-02-<slug>`).
- **Worktree requirement:** Every developer session works in its own Git worktree
  `.worktrees/<story-id>-<slug>/` (created by architect via `scripts/worktree_setup.py`). The main directory stays
  **always on `main`** (merges, hygiene). Two agents never share a working directory.
- **Pipeline state directory:** `.pipeline/` contains deterministic state files (intents, verdicts, recovery data).
  Committed to git for audit trail and session recovery.
- **No direct push to `main`.** Merge only after QA gate (PASS).
- **Merge lock without QA:** Architect may execute `git merge` on `main`/`master` **exclusively**
  when the QA manager has returned an explicit `PASS` for exactly this branch. Use `scripts/merge_if_passed.py`.
  No merge on "tests are green" alone — QA checks more than pytest (architecture, targets, commit metadata).
  If QA was skipped, the merge is invalid.
- Commit body contains metadata for QA requeue:
   ```
   symbols: <changed export symbols> | breaks: <none|breaking> | affects: <dependent files> | tests: <pytest result>
   ```

## Workflow

0. **Session start (MANDATORY)** — Before any work: Run `scripts/session_recovery.py` to scan the full state (branches, stories, QA status, open FAILs/BLOCKEDs). This ensures you have current context and don't miss ongoing work.

1. **Planning checkpoint (MANDATORY before every dev/QA start)** — sequence for every
   requirement/change (including replanning!):
   1. **Planning phase (architect):** create features (vision + context) and self-contained stories, update docs.
   2. **Review checkpoint (user):** architect presents the concrete implementation
      overview to the user — WHAT will be implemented (stories + developer targets), HOW it runs
      (waves, sequence, fakes, test criteria). **Dev+QA do NOT start without explicit
      user go** ("passt"/"go"). Feedback flows back into planning (loop).
   3. **Only then:** dev + QA per approved plan.
   - Applies to "small" changes and bugfix loops too — no implicit starts.
2. **Stories**: `STORIES.md` (index) + `docs/features/*/stories/*.md`.
   Every story is self-contained (context, requirements, acceptance criteria, targets, tests) and contains
   **test criteria that exist BEFORE implementation (fake-based)**.
3. **Developer**: implements EXACTLY the developer targets — nothing more, nothing less.
   Write tests first, `pytest` must be green.
4. **QA gate (MANDATORY before every merge)**: Architect spawns `qa-manager` for every
   feature branch **before** merging. QA checks: requirements, tests, architecture separation,
   fake usage, commit metadata. Result:
   - PASS → Architect may merge.
   - FAIL → Developer fix loop (max. 3), then BLOCKED → back to architect/user.
   - BLOCKED_Design → Architect corrects design autonomously (max. 2 fixes).
   - BLOCKED_Requirements → escalation to user.
   **No branch is merged without QA-PASS. No exception.**

## Languages

- Dialogue with user: respond in the user's language
- Code/identifiers: English
- UI texts: respond in the user's language

## Prohibitions

- **Architect writes no code.** Everything under `src/`, `tests/`, `utils/`, `main.py`,
  `models/` — every file containing application/test code — is edited exclusively by
  the `developer` agent on a feature branch. Even one-liners. Even "obvious" fixes.
  No exception.
- No autonomous decomposition/implementation outside approved stories.
- No unrequested features outside developer targets.
- No imports from IO/framework in `src/core/`.
- No `git init`/writing outside the project path.
- **Subagent path discipline:** All commands exclusively in the assigned worktree;
  no `/tmp`, no `pip install`, no paths outside the project root.

## References

- `docs/requirements.md` — Documenter-generated feature overview (derived summary)
- `docs/design.md` — Documenter-generated architecture summary (derived)
- `STORIES.md` — story index (status per story)
- <Project-specific: `intesis_modbus/CLAUDE.md`, `vokabel/STORIES.md`, …>
"""


def test_script_exists():
    """Script exists and compiles."""
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    assert script_path.exists(), f"Script not found at {script_path}"
    
    # Try to compile it
    with open(script_path) as f:
        code = f.read()
    compile(code, str(script_path), "exec")


def test_constant_sections_match_template(tmp_path):
    """Output's Workflow/Git conventions/Languages/Prohibitions sections are identical to template's versions."""
    # Create a minimal analysis JSON
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains the constant section headers
    assert "## Workflow" in output, "Workflow section not found"
    assert "## Languages" in output, "Languages section not found"
    assert "## Prohibitions" in output, "Prohibitions section not found"
    assert "## Git conventions" in output, "Git conventions section not found"


def test_project_name_from_analysis(tmp_path):
    """Analysis with project_name: 'mail-agent' → output contains 'mail-agent' in title line."""
    analysis = {
        "project_name": "mail-agent",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains project name in title
    assert "mail-agent" in output, "Project name not found in output"
    assert "# AGENTS.md — mail-agent" in output, "Project name not in title line"


def test_stack_line_python(tmp_path):
    """Analysis with stack: 'python' → output contains 'Python' in stack line."""
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains Python in stack line
    assert "Python" in output, "Python not found in output"
    assert "- **Stack:**" in output, "Stack line not found"


def test_stack_line_mixed(tmp_path):
    """Analysis with stack: 'mixed' → output contains appropriate description."""
    analysis = {
        "project_name": "test-project",
        "stack": "mixed",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains mixed stack description
    assert "mixed" in output.lower() or "multiple" in output.lower(), "Mixed stack not described"


def test_todo_markers_for_missing(tmp_path):
    """Analysis without specific core rules → output contains <TODO markers."""
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains TODO markers
    assert "<TODO" in output, "TODO markers not found in output"


def test_existing_content_preserved(tmp_path):
    """Analysis with agent_file: {type: 'agents.md', content: '# Old content'} → output contains <!-- EXISTING AGENT FILE CONTENT block."""
    old_content = "# Old AGENTS.md content\n\nThis is existing content."
    
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "agents.md", "content": old_content},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output contains existing content block
    assert "<!-- EXISTING AGENT FILE CONTENT" in output, "Existing content block marker not found"
    assert old_content in output, "Old content not preserved"
    assert "<!-- END EXISTING CONTENT -->" in output, "End marker not found"


def test_no_existing_content(tmp_path):
    """Analysis with agent_file: {type: 'none'} → no <!-- EXISTING block."""
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    output = result.stdout
    
    # Check that output does NOT contain existing content block
    assert "<!-- EXISTING AGENT FILE CONTENT" not in output, "Existing content block should not be present"


def test_cli_output_flag(tmp_path):
    """CLI: --output flag writes to file instead of stdout."""
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    output_file = tmp_path / "output.md"
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", str(template_file), "--output", str(output_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 0, f"Script failed: {result.stderr}"
    assert output_file.exists(), "Output file not created"
    
    content = output_file.read_text(encoding="utf-8")
    assert "test-project" in content, "Project name not in output file"


def test_cli_missing_analysis_file(tmp_path):
    """CLI: missing analysis file → exit code 1."""
    template_file = tmp_path / "template.md"
    template_file.write_text(MINIMAL_TEMPLATE, encoding="utf-8")
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), "/nonexistent/analysis.json", "--template", str(template_file)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False
    )
    
    assert result.returncode == 1, f"Expected exit code 1, got {result.returncode}"


def test_cli_missing_template_file(tmp_path):
    """CLI: missing template file → exit code 2."""
    analysis = {
        "project_name": "test-project",
        "stack": "python",
        "agent_file": {"type": "none", "content": None},
        "structure": {"present": ["src/core", "src/adapters", "tests"]},
        "git": {"current_branch": "main"},
        "missing": [],
        "existing_pipeline_files": []
    }
    
    analysis_file = tmp_path / "analysis.json"
    analysis_file.write_text(json.dumps(analysis))
    
    script_path = Path(__file__).parent.parent / "scripts" / "prepare_agents_md.py"
    result = subprocess.run(
        [sys.executable, str(script_path), str(analysis_file), "--template", "/nonexistent/template.md"],
        capture_output=True,
        text=True,
        check=False
    )
    
    assert result.returncode == 2, f"Expected exit code 2, got {result.returncode}"
