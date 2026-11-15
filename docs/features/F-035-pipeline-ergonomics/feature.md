---
id: F-035
title: Pipeline Ergonomics
status: planned
owner: ""
req: []
---

## Vision

Small friction points removed: a cosmetic SyntaxWarning in
`worktree_setup.py` is fixed; the architect's manual-reconcile fallback
(when the documenter subagent hits a usage limit) is documented in
AGENTS.md so no session is left guessing what to do.

## Context

VirtOffice session 2026-11-15 (story 51-01): documenter subagent hit an
Ollama usage limit; merge was blocked because `merge_if_passed.py`
requires a `docs: reconcile` commit, and no fallback path was documented.
The architect fell back to a manual reconcile but the valid procedure was
undefined. Additionally, `worktree_setup.py` emits a Python
SyntaxWarning (`'\s'` → should be `r'\s'`) that is cosmetic but noisy.
See also TODO.md → T-003.

## Stories

- 01-01-ergonomics-fixes (planned)
- 35-01-ergonomics-fixes (Planned)
