# Story 06-12 — Agent prompt updates for script integration

Status: Planned
Traceability: REQ-013, NFR-004 → Design §13

## Definition

Update all agent prompts (architect, developer, qa-manager) to call deterministic scripts
instead of performing operations free-hand. Also update commands to reference scripts.

## Development goal

After this story, all agent prompts instruct agents to use scripts for git operations,
status aggregation, story management, and QA routing. The LLM ↔ Script boundary (NFR-004)
is enforced in the prompts.

## Developer Targets (exactly, no more / no less)

- Update `agent/architect.md`:
  - Use `scripts/worktree_setup.py` instead of manual `git worktree add`
  - Use `scripts/create_story.py` instead of manual story file creation
  - Use `scripts/resolve_story.py` for story lookups
  - Use `scripts/merge_if_passed.py` instead of manual `git merge`
  - Use `scripts/promote_release.py` for release promotion
  - Run `scripts/session_recovery.py` at session start
  - Write intents via `scripts/intent.py` before actions

- Update `agent/developer.md`:
  - Use `scripts/prepare_commit_metadata.py` for commit messages
  - Use `scripts/intent.py` to track current step
  - Use `scripts/resolve_story.py` to find story context

- Update `agent/qa-manager.md`:
  - Use `scripts/qa_route.py` for verdict recording and routing
  - Use `scripts/pipeline_status.py` for status aggregation
  - Spawn documenter after PASS (already in 06-10, verify consistency)
  - Use `scripts/merge_if_passed.py` reference for architect

- Update relevant commands (`command/implement.md`, `command/qa-check.md`,
  `command/status.md`, `command/new-project.md`, `command/decompose.md`):
  - Reference corresponding scripts instead of free-hand instructions

- Update `templates/AGENTS.md`:
  - Add session-recovery instruction to constant Workflow section
  - Reference `.pipeline/` directory in Git conventions

## Acceptance criteria (checked by qa-manager)

- All three agent prompts reference the correct scripts
- No agent prompt instructs free-hand git worktree/branch/merge operations
- All commands reference scripts where applicable
- Session recovery instruction is in agent prompts
- Intent tracking instruction is in agent prompts
- Template AGENTS.md updated with new conventions
- No concrete model/provider names introduced

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_prompt_scripts.py::test_architect_references_scripts` — architect.md contains references to worktree_setup, create_story, resolve_story, merge_if_passed, session_recovery, intent
- `tests/test_prompt_scripts.py::test_developer_references_scripts` — developer.md contains references to prepare_commit_metadata, intent, resolve_story
- `tests/test_prompt_scripts.py::test_qa_manager_references_scripts` — qa-manager.md contains references to qa_route, pipeline_status
- `tests/test_prompt_scripts.py::test_no_freehand_git_worktree` — no agent prompt contains `git worktree add` as a direct instruction
- `tests/test_prompt_scripts.py::test_template_has_recovery` — templates/AGENTS.md references session_recovery
- `tests/test_prompt_scripts.py::test_no_model_names` — existing model-name check still passes
