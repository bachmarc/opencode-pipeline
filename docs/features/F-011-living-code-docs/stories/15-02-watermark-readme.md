# Story 15-02 — Watermark in README and AGENTS.md

Status: Planned
Feature: living-code-docs (F-011)

## Context / Purpose

README.md (human-readable system overview) and AGENTS.md (LLM-readable project knowledge)
describe the current system state but have no mechanism to track which changes have been
incorporated. When the Documenter runs, it must re-evaluate the entire document against
the entire codebase — a task that produces drift because the scope is unbounded.

By adding a `synced_through` watermark to both files, the Documenter can determine exactly
which stories have been incorporated and which are pending. This enables incremental
updates: read only the new stories, check the affected code's docstrings, update the
relevant sections. No full re-evaluation needed.

The watermark is a YAML comment block at the top of each file (after the title) containing
the last incorporated story ID and timestamp.

## Requirements

1. README.md must contain a watermark comment indicating the last synced story ID.
2. AGENTS.md must contain a watermark comment indicating the last synced story ID.
3. The watermark format must be parseable by scripts (for the Documenter to read).
4. A test must verify both files contain a valid watermark.
5. A helper script must exist to read the current watermark and list pending stories.

## Developer Targets (exactly, no more / no less)

- `README.md`: Add watermark block after the title line. Format:
  ```
  <!-- synced_through: 14-01 | updated: 2026-09-22 -->
  ```
  Place it on line 2 (after `# opencode Pipeline`), as an HTML comment so it doesn't
  render visually but is parseable.

- `AGENTS.md`: Add same watermark format after the title line.
  ```
  <!-- synced_through: 14-01 | updated: 2026-09-22 -->
  ```

- `scripts/check_watermark.py`: New script that:
  1. Reads the watermark from a given file (parse the HTML comment)
  2. Reads STORIES.md to find all done stories
  3. Returns JSON: `{"file": "...", "synced_through": "14-01", "pending_stories": ["15-01", ...]}`
  4. Exit code 0 if up to date, 1 if stories are pending
  Accepts `--file <path>` argument. If no argument, checks both README.md and AGENTS.md.

- `tests/test_watermark.py`: New test file with:
  - `test_readme_has_watermark` — README.md contains parseable watermark comment
  - `test_agents_md_has_watermark` — AGENTS.md contains parseable watermark comment
  - `test_watermark_format_valid` — watermark matches expected regex pattern
  - `test_check_watermark_script_runs` — script executes without error and returns valid JSON
  - `test_check_watermark_detects_pending` — given a watermark behind current stories,
    script reports pending stories correctly

## Acceptance criteria (checked by qa-manager)

- README.md contains a parseable `synced_through` watermark on line 2
- AGENTS.md contains a parseable `synced_through` watermark on line 2
- `scripts/check_watermark.py` exists, runs, and returns valid JSON
- Script correctly identifies pending stories when watermark is behind
- All new tests pass, all existing tests remain green
- No model/provider names introduced in any changed file
- Watermark does not visually render in Markdown viewers (HTML comment)

## Test criteria (must exist BEFORE implementation)

- `tests/test_watermark.py::test_readme_has_watermark` — README.md line 2 matches
  `<!-- synced_through: ... | updated: ... -->`
- `tests/test_watermark.py::test_agents_md_has_watermark` — AGENTS.md line 2 matches
  same pattern
- `tests/test_watermark.py::test_watermark_format_valid` — regex
  `<!-- synced_through: \d{2}-\d{2} \| updated: \d{4}-\d{2}-\d{2} -->` matches
- `tests/test_watermark.py::test_check_watermark_script_runs` — subprocess call returns
  exit 0 and valid JSON with keys `file`, `synced_through`, `pending_stories`
- `tests/test_watermark.py::test_check_watermark_detects_pending` — mock a watermark
  at an older story, verify `pending_stories` is non-empty
