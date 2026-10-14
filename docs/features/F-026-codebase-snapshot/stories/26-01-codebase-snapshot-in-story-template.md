# Story 26-01 — Codebase Snapshot in Story Template

Status: Planned
Feature: Codebase Snapshot in Stories (F-026)

## Context / Purpose

When the Architect decomposes a feature into stories, they already explore the relevant codebase: which files are affected, which functions are entry points, which tests already exist nearby. This knowledge currently exists only in the Architect's session and is gone by the time the Developer starts.

The Developer re-explores the same codebase from scratch before writing a single line — reading the same files, running the same greps. This duplication costs tokens and time on every story.

The fix: the Architect writes down what they found as part of the story itself, in a `## Codebase Snapshot` section. The Developer reads it first and starts immediately. The snapshot is produced by the Architect at decomposition time — not as a separate step, but as part of writing the story.

## Codebase Snapshot

- `docs/features/_story_template.md` — 28 lines, currently 5 sections (Context, Requirements, Developer Targets, Acceptance criteria, Test criteria). New section `## Codebase Snapshot` added between the header block and `## Context / Purpose`.
- `agents/architect.md` — "Decompose features & stories" task block (lines ~40–80). Rule for snapshot to be added here.
- `agents/developer.md` — Workflow step 1 (line 17: "Read your story file"). Snapshot consumption rule added here.
- `tests/test_templates.py` — existing template section tests (lines 7–95). New test added here.
- `tests/test_architect_prompt.py` — existing architect rule tests (lines ~100–130). Two new tests added here: snapshot rule + test scenario review rule.
- `tests/test_developer_prompt.py` — existing developer rule tests. New test added here.

## Requirements

**Story template** (`docs/features/_story_template.md`):

Add `## Codebase Snapshot` as a new section between the header block and `## Context / Purpose`:

```markdown
## Codebase Snapshot

<!-- Filled by Architect at decomposition time. Lists affected files, relevant function
     signatures, and existing tests near the change. Developer reads this first.
     Omit only for trivial one-liners with no existing code to navigate. -->

- `<file>` — <what is in it that is relevant: function name, line range, what it does>
- `<test file>` — <which existing tests cover adjacent code>
```

The section is optional by convention (can be omitted for trivial changes) but present in the template so the Architect sees it as a prompt.

**Architect prompt** (`agents/architect.md`):

In the "Decompose features & stories" task block, add two rules:

> **Codebase Snapshot (mandatory for stories touching existing code):** When writing a story for a feature that modifies existing files, explore the relevant files and add a `## Codebase Snapshot` section to the story. List: affected files with the relevant function names and line ranges, and any existing test files that cover adjacent code. Write this as part of story decomposition — not as a separate step. Omit only for stories that create entirely new files with no existing code to navigate.

> **Test scenario review (at Planning Checkpoint):** When presenting the implementation overview to the user, include the non-trivial test scenarios and briefly explain why each one is meaningful — what behavior or edge case it protects. Skip explanation for trivial checks (file exists, string present). The goal is that the user can spot "this test checks the wrong thing" or "this edge case is missing" before implementation starts.

**Developer prompt** (`agents/developer.md`):

In Workflow step 1 ("Read your story file"), extend to:

> If the story contains a `## Codebase Snapshot` section, read it before exploring any files. Use it as your navigation starting point — go directly to the listed files and functions. Do not re-explore files already covered by the snapshot.

## Developer Targets (exactly, no more / no less)

- `docs/features/_story_template.md` — insert `## Codebase Snapshot` section (with comment and example placeholder) between the header block and `## Context / Purpose`. Update no other sections.
- `agents/architect.md` — add Codebase Snapshot rule and test scenario review rule to the "Decompose features & stories" task block. Update no other sections.
- `agents/developer.md` — extend Workflow step 1 with snapshot consumption instruction. Update no other sections.
- `tests/test_templates.py` — add `test_story_template_has_codebase_snapshot_section()`: reads `docs/features/_story_template.md`, asserts `## Codebase Snapshot` is present.
- `tests/test_architect_prompt.py` — add `test_architect_prompt_has_codebase_snapshot_rule()` and `test_architect_prompt_has_test_scenario_review_rule()`: read `agents/architect.md`, assert respective content present.
- `tests/test_developer_prompt.py` — add `test_developer_prompt_reads_codebase_snapshot()`: reads `agents/developer.md`, asserts it contains `Codebase Snapshot`.

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `docs/features/_story_template.md` contains `## Codebase Snapshot` section before `## Context / Purpose`.
- `## Codebase Snapshot` section contains a comment explaining its purpose and an example placeholder line.
- `agents/architect.md` contains a rule about filling the Codebase Snapshot at decomposition time.
- `agents/architect.md` contains a rule about presenting non-trivial test scenarios with explanation at the Planning Checkpoint.
- `agents/developer.md` contains a rule about reading the Codebase Snapshot before exploring files.
- All three new tests pass.
- All existing tests pass (no regression — existing section checks still hold).

## Test criteria (must exist BEFORE implementation)

- `tests/test_templates.py::test_story_template_has_codebase_snapshot_section` — reads `docs/features/_story_template.md`, asserts `## Codebase Snapshot` present
- `tests/test_architect_prompt.py::test_architect_prompt_has_codebase_snapshot_rule` — reads `agents/architect.md`, asserts `Codebase Snapshot` present
- `tests/test_architect_prompt.py::test_architect_prompt_has_test_scenario_review_rule` — reads `agents/architect.md`, asserts it contains guidance about presenting test scenarios at the Planning Checkpoint
- `tests/test_developer_prompt.py::test_developer_prompt_reads_codebase_snapshot` — reads `agents/developer.md`, asserts `Codebase Snapshot` present
