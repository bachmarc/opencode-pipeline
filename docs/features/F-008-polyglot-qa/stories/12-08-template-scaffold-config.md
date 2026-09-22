# Story 12-08 — Template config sections + scaffold + own qa_config.json

Status: Done
Feature: polyglot-qa (F-008)

## Context / Purpose

The **constant** sections of `templates/AGENTS.md` hard-name pytest
("Write tests first, `pytest` must be green", `tests: <pytest result>`) —
binding for every project, so a Java project would be contractually forced to
pytest. The scaffold script creates Python-flavored `tests/`, `src/core`,
`src/adapters` dirs unconditionally, and this repo has no `qa_config.json`
yet. This story makes the template runner-agnostic and scaffolds
`qa_config.json`.

**Breaking change, deliberately:** changing the constant sections means
existing project AGENTS.md files (netclip, vokabel, …) fail the constancy
check until re-synced once (handled by 12-09's migration tool + release note).

## Requirements

- `templates/AGENTS.md` constant sections genericized:
  - Workflow §3: "Write tests first, `pytest` must be green." → "Write tests
    first, the project's configured test suite must be green."
  - Git conventions commit metadata: `tests: <pytest result>` →
    `tests: <test suite result>`.
  - Everything else in the constant sections byte-identical (constancy
    check + test_check_scripts must stay green against the new template).
- `templates/AGENTS.md` project-specific section gains a placeholder line:
  - **Stack:** `<...>`, test stack: `<runner> — declared in qa_config.json
    (checkers list)`
  - Plus one core-rule line: "The project's `qa_config.json` declares the
    QA checkers; missing file → pytest default."
- `scripts/scaffold_project.py`:
  - Creates `qa_config.json` in new projects. Default:
    `{"checkers": ["pytest"]}` (framework scaffold default — architect/user
    adapts per project stack).
  - Directory layout becomes stack-aware: `tests/`, `tests/fakes/`,
    `src/core/`, `src/adapters/` only when the stack hint says Python;
    otherwise neutral dirs (`docs/`, `src/` flat) — scaffold stays
    deterministic, no stack guessing: add CLI flag `--stack
    <python|ruby|javascript|java|mixed>` with default `python`, mapping to
    dir sets. `--stack mixed` creates only `docs/` + `src/` + `tests/`.
  - `AGENTS.md` copied from template as before (placeholders unfilled —
    filling is architect dialogue, unchanged).
- This repo (opencode-pipeline) gets its own `qa_config.json`:
  `{"checkers": ["pytest", "yaml"]}` — dogfoods the gate on its own
  frontmatter (yaml checker from 12-04).

## Developer Targets (exactly, no more / no less)

- Edit `templates/AGENTS.md`: the two genericized lines in constant
  sections; stack placeholder + core-rule line in "This project" section;
  nothing else.
- Edit `tests/test_check_scripts.py::test_template_constancy_fail` fixture
  content: align the embedded project-AGENTS.md fixture with the new template
  constant sections (keep "MODIFIED LINE" in Prohibitions so the test still
  FAILs on the right section).
- Edit `scripts/scaffold_project.py`: `--stack` flag with the 5 values,
  dir-set mapping (`python`: current set; `ruby`: `spec/`, `docs/`,
  `src/`; `javascript`: `test/`, `docs/`, `src/`; `java`: `src/test`,
  `src/main`, `docs/`; `mixed`: `docs/`, `src/`, `tests/`), and
  `qa_config.json` creation (default `{"checkers": ["pytest"]}`).
- Create repo-root `qa_config.json` with `{"checkers": ["pytest", "yaml"]}`.
- `tests/test_scaffold_stack.py` (see test criteria).

## Acceptance criteria (checked by qa-manager)

- `templates/AGENTS.md` contains no runner name in constant sections
  (`pytest` absent from Workflow/Git/Languages/Prohibitions sections; the
  core-rule line mentioning the default is in the project-specific section,
  not a constant one).
- `check_template_constancy.py` PASSes a project AGENTS.md that is
  identical-to-new-template; `test_check_scripts.py` green.
- Scaffold `--stack python` → old dir set + `qa_config.json` exists;
  `--stack java` → `src/test`, `src/main` dirs, no `tests/fakes`.
- Scaffolded `qa_config.json` parses and contains a `checkers` list.
- Repo `qa_config.json` exists with `["pytest", "yaml"]`; `qa_compress.sh`
  in repo root now runs pytest + yaml checkers (integration proof —
  frontmatter of this repo stays valid).
- Existing self-checks green; no model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_scaffold_stack.py` — tmp_path targets:

- `test_scaffold_default_python` — no flag → `tests/fakes/`, `src/core/`,
  `src/adapters/` exist; `qa_config.json` exists and equals
  `{"checkers": ["pytest"]}`.
- `test_scaffold_stack_ruby` — `--stack ruby` → `spec/` exists, no
  `src/core/`; `qa_config.json` present.
- `test_scaffold_stack_java` — `--stack java` → `src/main`, `src/test`
  exist; no `tests/` dir.
- `test_scaffold_stack_mixed` — `--stack mixed` → `docs/`, `src/`, `tests/`
  exist; no `src/core/`.
- `test_qa_config_committed` — repo's own root `qa_config.json` parses,
  `checkers == ["pytest", "yaml"]`.

`tests/test_check_scripts.py` — updated fixture (red first: old fixture
would now PASS under new template → test invalid; updated fixture keeps the
intended FAIL-on-Prohibitions semantics).