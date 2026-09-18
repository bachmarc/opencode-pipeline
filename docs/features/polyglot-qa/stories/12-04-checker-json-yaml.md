# Story 12-04 — Checker plugins: JSON + YAML syntax validation

Status: Planned
Feature: polyglot-qa (F-008)

## Context / Purpose

The user's projects are config-heavy: JSON and YAML files appear constantly.
Broken JSON/YAML breaks deploys and tools at runtime — the QA gate should catch
syntax errors deterministically before merge. This is a syntax check, NOT a
schema validation: only well-formedness is checked. Both checkers are dogfooded
immediately — the pipeline repo itself contains JSON (pyproject, frontmatter-adjacent
files) and can use `yaml` for `docs/features/*/feature.md` frontmatter validation
once available.

## Requirements

- Checker `json`: validates syntax of all `*.json` files in the project cwd.
  - Walks the tree from cwd, excluding the pipeline's own directories:
    `.git`, `.pipeline`, `.worktrees`, `node_modules`, `__pycache__`,
    `.pytest_cache`, `dist`, `build`.
  - Skips `.gitignore`d files if a cheap deterministic way exists in stdlib
    (else document the exclusion list as the contract — no new dependencies).
  - Each invalid file → one line `INVALID <path>` under `## failed_files`,
    ≤20; overall FAIL.
  - Valid repo → summary `N files checked, 0 invalid`, exit 0.
- Checker `yaml`: same walk/exclusions; each invalid file → `INVALID <path>`
  under `## failed_files`, ≤20; overall FAIL on any.
- Both use **python3 stdlib only** (`json`, `pathlib`) or the `yaml` third-party
  module for YAML parsing (`PyYAML` pinned in `requirements.txt` — a framework
  prerequisite, like python3 itself). If PyYAML is unavailable at runtime, the
  yaml checker must FAIL loudly (`yaml checker: PyYAML not installed`) instead
  of silently skipping.
- Plugin contract as in 12-02/12-03: self-registering files in
  `scripts/qa_checkers/`, no shared-file edits.
- Dogfood: add `yaml` to this repo's own `qa_config.json` (created in 12-08) so
  the pipeline validates its own feature frontmatter from now on.

## Developer Targets (exactly, no more / no less)

- `scripts/qa_checkers/json.sh`: `json_check()` — iterates `**/*.json` under
  cwd (bash glob or python3 one-liner), excluding the listed dirs; each file
  parsed via `python3 -c "import json,sys; json.load(open(sys.argv[1]))" <file>`;
  collects invalid paths; summary line `N files checked, M invalid`; on
  invalid >0: `## failed_files` + `INVALID <path>` lines (≤20) → exit 1; else
  exit 0; then `register_check json json_check`.
- `scripts/qa_checkers/yaml.sh`: `yaml_check()` — same walk; parse via
  `python3 -c "import yaml; yaml.safe_load(open(...))"`; if import fails →
  print `yaml checker: PyYAML not installed`, exit 1; same summary/failed list;
  `register_check yaml yaml_check`.
- Add `PyYAML` (pinned, e.g. `PyYAML==6.0.2`) to `requirements.txt`.
- `tests/test_qa_checkers_json_yaml.py` (see test criteria).

## Acceptance criteria (checked by alpha-manager)

- Project with valid JSON files only → `json` checker PASS, summary
  `N files checked, 0 invalid`.
- One broken JSON file (e.g. missing brace) → FAIL, `INVALID <path>` listed.
- Broken YAML (bad indentation) → FAIL under `yaml` checker.
- Both checkers in one config (`["json", "yaml"]`) → serial run, both PASS on
  a clean repo → overall PASS.
- Exclusion dirs are NOT walked (create `.worktrees/broken.json` → still PASS).
- PyYAML import failure path → loud FAIL, not silent skip.
- Existing checkers unchanged; 12-01..12-03 tests green; `bash -n` clean; no
  model/provider names.

## Test criteria (must exist BEFORE implementation)

`tests/test_qa_checkers_json_yaml.py` — tmp_path project roots:

- `test_json_pass` — config `["json"]`; create `cfg.json` (valid) and
  `data/nested.json` (valid) → overall PASS, summary contains
  `2 files checked, 0 invalid`.
- `test_json_fail` — add `broken.json` (`{"a": 1` missing brace) → overall
  FAIL, output contains `INVALID broken.json` under `## failed_files`.
- `test_json_excludes_pipeline_dirs` — create `.worktrees/x/broken.json` →
  checker still PASS (excluded).
- `test_yaml_pass` — valid `feature.md`-style frontmatter YAML file → PASS.
- `test_yaml_fail` — `key: [unclosed` → FAIL, `INVALID` listed.
- `test_yaml_missing_pyyaml` — call the yaml checker directly in an
  environment where the `yaml` import fails (e.g. stub python3 on PATH that
  fails on `import yaml`) → output contains `PyYAML not installed`, exit 1.