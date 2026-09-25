# Story 21-02 — Documenter catch-up run (Stories 15-xx through 20-xx)

Status: Planned
Feature: documenter-scope-fix (F-021)

## Context / Purpose

Since Story 12-09 (2026-09-18), the Documenter has not run on any merged story. The scope
bug in `merge_if_passed.py` (fixed in 21-01) allowed all merges to pass without a
`docs: reconcile` commit on the feature branch. As a result, `README.md` and `AGENTS.md`
carry watermark `synced_through: 14-01` while Stories 15-00 through 20-03 (18 stories across
6 phases) are unrecorded.

This story is a one-time catch-up: the Documenter agent runs on `main`, reads all pending
stories via `check_watermark.py`, updates `README.md` and `AGENTS.md`, and commits with
`docs: reconcile 15-00..20-03`.

This story has no code changes — it is purely a Documenter agent run + commit on `main`.
It is implemented by spawning the Documenter agent (not a developer).

## Requirements

1. `README.md` accurately reflects the framework state after Stories 15-00 through 20-03.
2. `AGENTS.md` accurately reflects the framework state after Stories 15-00 through 20-03.
3. Both files carry watermark `synced_through: 20-03` (or the highest merged story ID).
4. A single commit `docs: reconcile 15-00..20-03` exists on `main`.

## Developer Targets (exactly, no more / no less)

This story is implemented by the **Documenter agent**, not the developer agent.

- Run `check_watermark.py` to identify all pending stories (15-00 through 20-03).
- For each pending story: read story file, identify changed files from Developer Targets,
  read docstrings/headers from those files.
- Update `README.md` — revise all sections affected by the 18 pending stories.
- Update `AGENTS.md` — revise all sections affected by the 18 pending stories.
- Bump `synced_through` watermark in both files to `20-03`.
- Commit on `main` with message: `docs: reconcile 15-00..20-03`

## Acceptance criteria (checked by qa-manager)

- No `[NEEDS CLARIFICATION]` markers remain in this story.
- `README.md` line 2 contains `synced_through: 20-03`.
- `AGENTS.md` line 2 contains `synced_through: 20-03`.
- Commit `docs: reconcile 15-00..20-03` exists on `main`.
- `README.md` mentions the Python QA toolchain (`qa_compress.py`).
- `README.md` mentions the pipeline enforcement plugin.
- `AGENTS.md` mentions `qa_compress.py` as the mandatory test entry point.
- `check_watermark.py` reports no pending stories after the commit.

## Test criteria (must exist BEFORE implementation)

This story has no automated tests — it is a documentation-only commit verified by
the acceptance criteria above (grep-verifiable watermark + content checks).
QA verifies manually: `check_watermark.py` output + grep for key terms in README/AGENTS.
