# Story 06-13 — Template constancy and architecture check scripts

Status: Planned
Traceability: REQ-013.4, REQ-013.11 → Design §13

## Definition

Two scripts that extend the QA pipeline: template constancy checking for projects created
by the pipeline, and AST-based architecture validation (import rules for src/core/).

## Development goal

After this story, template constancy and architecture rules are deterministically
verifiable by script — not by LLM visual inspection.

## Developer Targets (exactly, no more / no less)

- Create `scripts/check_template_constancy.py`:
  - `check_template_constancy.py <project-agents-md>`:
    - Extracts constant sections (Workflow, Git conventions, Languages, Prohibitions)
      from `templates/AGENTS.md` (source of truth)
    - Extracts same sections from provided project AGENTS.md
    - Compares them (ignoring leading/trailing whitespace per line)
    - If identical: exit 0 + `{"result": "PASS"}`
    - If different: exit 1 + `{"result": "FAIL", "sections": ["Languages"], "diff": "..."}`
  - Section boundaries defined by `## ` heading markers

- Create `scripts/check_architecture.py`:
  - `check_architecture.py <src-core-path> [--allowlist <file>]`:
    - Uses Python `ast` module to parse all `.py` files in `src/core/`
    - Extracts all import statements
    - Checks against allowlist (stdlib modules + explicitly allowed)
    - If clean: exit 0 + `{"result": "PASS", "files_checked": N}`
    - If violations: exit 1 + `{"result": "FAIL", "violations": [{"file": "...", "import": "...", "line": N}]}`
  - Default allowlist: Python stdlib modules
  - Custom allowlist file: one module per line

- Both scripts use only stdlib

## Acceptance criteria (checked by qa-manager)

- Template constancy check detects modified constant sections
- Template constancy check passes for unmodified sections
- Architecture check detects forbidden imports
- Architecture check passes for clean core modules
- Both output valid JSON with PASS/FAIL result

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_check_scripts.py::test_template_constancy_pass` — identical sections → PASS
- `tests/test_check_scripts.py::test_template_constancy_fail` — modified section → FAIL with section name
- `tests/test_check_scripts.py::test_architecture_check_clean` — stdlib-only imports → PASS
- `tests/test_check_scripts.py::test_architecture_check_violation` — forbidden import → FAIL with file/line
- `tests/test_check_scripts.py::test_architecture_check_allowlist` — allowed import not flagged
- `tests/test_check_scripts.py::test_scripts_exist` — both scripts exist and compile
