---
id: "22-02"
feature: F-022
title: "Developer prompt: forbid post-commit qa_compress.py verification run"
status: planned
branch: feature/22-02-developer-no-postcommit-run
---

## Context

The developer agent runs `qa_compress.py` once before committing (correct) and then again
after committing "to verify" (wasteful — adds ~85s and burns tokens for no new
information). The prompt must explicitly forbid this pattern.

## Requirements

1. `agent/developer.md` explicitly states: run `qa_compress.py` exactly once before
   committing; do NOT run it again after the commit.
2. The prohibition is unambiguous — "do not run qa_compress.py after committing" or
   equivalent.

## Developer Targets

- `agent/developer.md`: in the test/commit step, add explicit note:
  "Run `qa_compress.py` exactly once before committing. Do NOT run it again after the
  commit — the pre-commit run is the QA evidence."
- Update the module header/frontmatter description if it references the test workflow.

## Acceptance Criteria

- `agent/developer.md` contains a prohibition against post-commit `qa_compress.py` runs
  (grep-verifiable).
- All existing tests still pass.

## Test Criteria (before implementation)

- `tests/test_developer_prompt.py` (or equivalent): assert `agent/developer.md` contains
  the string "do not run" or "Do NOT run" near "qa_compress" or "after"
  (case-insensitive grep on file content).
