# Story 06-07 — Project scaffolding script

Status: Planned
Traceability: REQ-013.3 → Design §13

## Definition

Replace LLM free-hand project creation (`/new-project`) with a deterministic script that
copies real templates and creates the directory structure atomically. Only placeholder
filling (project name, description, stack) remains with the LLM.

## Development goal

After this story, `scripts/scaffold_project.py` creates a complete project skeleton by
copying templates and creating directories — no LLM text generation for structure.

## Developer Targets (exactly, no more / no less)

- Create `scripts/scaffold_project.py`:
  - `scaffold_project.py <target-path> [--name <project-name>]`
  - If target has no git repo: `git init` + `git checkout -b main`
  - Creates directories: `docs/`, `docs/features/`, `tests/`, `tests/fakes/`, `src/core/`, `src/adapters/`
  - Copies templates (real `shutil.copy`, not LLM):
    - `templates/AGENTS.md` → `<target>/AGENTS.md`
    - `docs/features/_story_template.md` → `<target>/docs/features/_story_template.md`
  - Creates empty starter files: `FEATURES.md`, `docs/requirements.md`, `docs/design.md`,
    `.gitignore` (from template), `README.md` (minimal header), `.pipeline/intent.json`
  - Outputs JSON: `{"created": ["<list of files>"], "target": "<path>"}`
  - Exit code 0 success, 1 target doesn't exist, 2 already scaffolded (has AGENTS.md)
- Create `templates/.gitignore` — standard gitignore template for pipeline projects
- Script uses only stdlib (shutil, pathlib, subprocess, json, argparse)

## Acceptance criteria (checked by qa-manager)

- Script creates all required directories and files
- Templates are byte-identical copies (not LLM re-generation)
- Script is idempotent-safe: refuses to overwrite if already scaffolded
- Git init only happens if no `.git/` exists
- Output lists all created files

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_scaffold.py::test_script_exists` — script exists and compiles
- `tests/test_scaffold.py::test_scaffold_creates_dirs` — all required directories exist after run
- `tests/test_scaffold.py::test_scaffold_copies_templates` — AGENTS.md in target matches source template
- `tests/test_scaffold.py::test_scaffold_git_init` — `.git/` exists after scaffolding empty dir
- `tests/test_scaffold.py::test_scaffold_already_exists` — exit code 2 when AGENTS.md already present
- `tests/test_scaffold.py::test_scaffold_output_json` — output is valid JSON with file list
