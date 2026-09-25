---
id: F-022
title: qa_compress Fast Mode
status: planned
owner: ""
req: []
---

## Vision

`qa_compress.py --fast` runs only the test modules that correspond to changed files (via
`git diff main..<branch> --name-only` → name-convention mapping `scripts/foo.py` →
`tests/test_foo.py`, `plugins/guards/foo.ts` → `tests/test_foo.py`). Full run remains
default. Developer prompt forbids post-commit verification runs.

## Context

Full suite takes ~85s. Developer wastes tokens running it twice. Fast mode cuts feedback
loop for focused changes.

## Stories

- 22-01: qa_compress.py --fast: changed files → affected test modules
- 22-02: Developer prompt: forbid post-commit qa_compress.py verification run
