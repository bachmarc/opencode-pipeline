# Story 30-05 — plan_check.py: deterministic planning QA

Status: Done
Feature: Process Driver (F-030)

## Codebase Snapshot

- `docs/features/*/stories/*.md` — story files: `Status:
  <Planned | In Progress | Done>` line + `## Section` headings
  (Context / Purpose, Requirements, Developer Targets, Acceptance criteria,
  Test criteria, Tooling Gates). These are the input documents — parsed,
  never trusted.
- `scripts/story_status.py` — existing `Status:` line parsing pattern for
  story files.
- `scripts/check_template_constancy.py`, `scripts/check_watermark.py` —
  existing deterministic check-script patterns (exit 0 PASS / 1 FAIL,
  section extraction from markdown).
- `tests/test_check_scripts.py` — existing test pattern for check scripts
  (verify actual coverage via grep; the new test file parallels it).
- `tests/test_story_status.py` — pattern for fixture story files in tmp_path.

## Context / Purpose

Planning is cheap-model territory — and flash-class planners make
mechanical mistakes. Real cases from THIS planning round (2026-10-30): a
story told the developer to "extend `tests/test_create_story.py`" — that file
never existed; two stories created `scripts/driver.py` on parallel branches;
two stories edited `agents/architect.md`. All three conflict classes went
unnoticed into the checkpoint. Every one is deterministically detectable
BEFORE dev start. This story adds the missing check script so the planning
checkpoint is machine-backed: weak models plan continuously and cheaply,
correctness is enforced by scripts, and the strong-model audit (F-031 tier
policy, escalation point "(a) planning audit") reviews only what scripts
cannot.

**Sequencing:** Wave-1-safe — this story creates ONLY new files
(`scripts/plan_check.py`, `tests/test_plan_check.py`). The
`agents/architect.md` prompt integration (run plan_check before every
checkpoint) ships in 30-04, not here — same-file discipline.

## Requirements

1. Create `scripts/plan_check.py` (stdlib-only, exit 0 PASS / 1 FAIL).
   Scans all `docs/features/*/stories/*.md`; single-story mode via
   `--story <file>`. OPEN stories only (`Status:` != `Done`) — Done stories
   are historical record, not checked.
   Checks:
   - **Ghost references:** every backticked token that resolves to a repo
     path (contains `/` or a known file suffix) AND is referenced as
     EXISTING (Codebase Snapshot lines; verbs "extend"/"existing") must
     exist in the repo. "Create <path>" targets are exempt (they are the
     story's own deliverables). **Sequenced cross-references** (audit fix
     2026-10-30): a path with extend/existing verbs that does NOT exist
     today but is a create-target of ANOTHER open story →
     `sequenced-reference` WARN entry (exit code unchanged), never a
     ghost-FAIL. Deterministic: create-target set = union of all open
     stories' Developer Targets "Create" lines (real case: 30-02 extends
     `scripts/driver.py`, which open 30-01 creates).
   - **Same-file conflicts:** build the touched-file set per story (paths
     in Developer Targets Create/Edit lines); a file touched by more than
     one OPEN story → `conflict_candidates` entry. Severity WARN (exit code
     unaffected) — the ARCHITECT resolves by declaring sequential waves in
     the STORIES.md phase block; the script does not guess ordering.
   - **Unresolved clarifications:** any `[NEEDS CLARIFICATION` marker in an
     open story → FAIL. Markers are resolved at the checkpoint, never
     carried into dev.
   - **Section completeness:** required sections present and non-empty:
     Context / Purpose; Requirements; Developer Targets; Acceptance
     criteria; Test criteria. Missing or empty → FAIL.
   Output JSON: `{result, problems: [{story, kind, detail}],
   conflict_candidates: [{file, stories}]}`.
2. Verb heuristic (extend/existing → must exist; create → exempt) and the
   JSON contract are documented in the module docstring — textual rules,
   no LLM, no guessing.
3. NO prompt/template changes in this story (`agents/architect.md`
   integration belongs to 30-04 — conflict discipline).

## Developer Targets (exactly, no more / no less)

- Create `scripts/plan_check.py` (module docstring: purpose, rules, verb
  heuristic, JSON contract, exit codes).
- Create `tests/test_plan_check.py` — fixture story files in `tmp_path`:
  ghost reference, conflict pair, clarification marker, empty section, Done
  story (skipped), clean story (passes).

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- Ghost reference: a fixture story referencing `tests/test_ghost.py` as
  existing → problem entry `{kind: "ghost-reference"}` and exit 1.
- Conflict detection: two fixture OPEN stories both touching
  `scripts/shared.py` → `conflict_candidates` entry naming both story ids;
  exit stays 0 when no other problems exist (WARN semantics).
- Unresolved `[NEEDS CLARIFICATION` in an open fixture story → exit 1.
- Done stories are not scanned (a Done fixture story with ghost refs does
  not fail).
- Clean story → `{result: PASS, problems: [], conflict_candidates: []}`,
  exit 0.
- Sequenced cross-reference (story extends a path that another OPEN story
  creates) → `sequenced-reference` WARN, exit unchanged (not ghost-FAIL).
- The script parses THIS repo's real story files without error (self-check:
  run against `docs/features/F-030-process-driver/stories/`).

## Test criteria (must exist BEFORE implementation)

- `tests/test_plan_check.py::test_ghost_reference_fails`
- `tests/test_plan_check.py::test_conflict_candidates_reported` — two open
  stories, same touched file → candidate entry, exit 0.
- `tests/test_plan_check.py::test_clarification_marker_fails`
- `tests/test_plan_check.py::test_missing_section_fails` — empty
  Requirements section → FAIL.
- `tests/test_plan_check.py::test_done_stories_skipped`
- `tests/test_plan_check.py::test_clean_story_passes`
- `tests/test_plan_check.py::test_single_story_mode`
- `tests/test_plan_check.py::test_sequenced_cross_reference_warns` — open
  story A creates `scripts/shared.py`, open story B extends
  `scripts/shared.py` → WARN `sequenced-reference`, exit unchanged (audit fix
  2026-10-30).

## Tooling Gates (mandatory — QA checks ALL of these)

Commands come from `qa_config.json` in the project root.

- [ ] Tests green (pytest)
- [ ] Lint clean (ruff)
- [ ] Typecheck clean (mypy) — if configured
- [ ] Format check clean (black)