# Story 15-04 — Dev-Start Guard Explicit Story Marker

Status: Planned
Feature: living-code-docs (F-011)

## Context / Purpose

The dev-start guard (`plugins/guards/dev-start-guard.ts`) extracts story IDs from the
developer/QA prompt using a blind regex `\b(\d{2}-\d{2})\b` that matches ANY number in
XX-YY format anywhere in the prompt text. This produces false positives when the prompt
mentions other story IDs in context (e.g., "watermark synced_through: 14-01" or
"depends on story 12-05").

The guard should only check the **target story** being implemented, not every number
that happens to match the pattern. The fix: require an explicit marker pattern at the
start of the prompt (e.g., `[story: 15-02]`) and only parse that. The architect prompt
must document this convention so spawned developer/QA prompts include the marker.

## Requirements

1. The dev-start guard must look for an explicit `[story: XX-YY]` marker in the prompt
   instead of matching all XX-YY patterns.
2. If no marker is found, the guard falls back to current behavior (match all — backward
   compatible) but adds a warning suggesting the marker format.
3. The architect prompt must document the marker convention for developer/QA spawns.
4. Existing tests must pass; new tests must cover the marker parsing.

## Developer Targets (exactly, no more / no less)

- `plugins/guards/dev-start-guard.ts`:
  - Add a new function `parseExplicitStoryId(prompt: string): string | null` that looks
    for `[story: XX-YY]` pattern (case-insensitive, allows whitespace variations).
  - Modify `devStartGuard()`: first try `parseExplicitStoryId()`. If found, only check
    that one story ID. If not found, fall back to current regex behavior but add a
    warning: "No [story: XX-YY] marker found in prompt. Using fallback pattern matching."
  - Update module docstring to document the marker convention.

- `agent/architect.md`:
  - Add guidance in the Phase 3 orchestration section: when spawning developer or
    QA-manager, include `[story: XX-YY]` at the start of the prompt.

- `tests/test_dev_start_guard.py` (existing file — add tests):
  - `test_explicit_marker_found` — prompt with `[story: 15-02]` marker only checks 15-02
  - `test_explicit_marker_ignores_other_ids` — prompt with marker `[story: 15-02]` and
    text mentioning "14-01" only checks 15-02, not 14-01
  - `test_fallback_without_marker` — prompt without marker falls back to current behavior
    and includes fallback warning
  - Update docstrings in changed files.

## Acceptance criteria (checked by qa-manager)

- Guard with `[story: 15-02]` marker only checks story 15-02, ignores other IDs in prompt
- Guard without marker falls back to current behavior with additional warning
- Architect prompt documents the `[story: XX-YY]` convention
- All existing dev-start-guard tests still pass
- New tests pass
- No model/provider names introduced

## Test criteria (must exist BEFORE implementation)

- `tests/test_dev_start_guard.py::test_explicit_marker_found` — prompt `[story: 15-02] implement...`
  returns warnings only about 15-02, not about other IDs in the text
- `tests/test_dev_start_guard.py::test_explicit_marker_ignores_other_ids` — prompt
  `[story: 15-02] watermark at 14-01` returns no warning about 14-01
- `tests/test_dev_start_guard.py::test_fallback_without_marker` — prompt without marker
  includes "fallback" in warnings
