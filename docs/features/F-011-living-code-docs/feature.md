---
id: F-011
title: Living Code Documentation
status: planned
owner: ""
req: []
---

## Vision

Code documentation is the source of truth. README.md and AGENTS.md stay current through
incremental updates guided by a watermark ("synced through story X"). The Documenter
knows exactly which stories to catch up on instead of re-evaluating everything from scratch.

## Context

After 10 features and 75+ stories, the pipeline has a knowledge gap: understanding the
current system state requires reading scattered feature files, story files, and the README.
The previous attempt at derived documentation (docs/design.md, docs/requirements.md) failed
because the Documenter had to re-evaluate the entire document against the entire codebase
each time — leading to drift and eventual deletion (F-010).

The root cause was identified: the Documenter had no way to know what changed since its
last run. It had to guess, and guessing at scale produces drift.

The fix is two-fold:

1. **Code-level documentation as Developer responsibility** — every story that changes code
   must update docstrings/headers in the changed files. The code itself becomes the
   authoritative source of truth at the function/module level.

2. **Watermark-based incremental updates for README.md and AGENTS.md** — these files carry
   a `synced_through` marker (last story ID that was incorporated). The Documenter reads
   only the stories since that marker, checks the affected code's docstrings, and makes
   targeted updates. No full re-evaluation, no drift.

This approach was inspired by OpenSpec's "living specs" concept but adapted to our
architecture: instead of a separate specs layer, we use the code itself (docstrings/headers)
as the ground truth and README/AGENTS.md as human-readable / LLM-readable synthesis.

### What this feature does NOT include

- No new `docs/specs/` directory or separate specification layer
- No changes to the feature/story file structure
- No automated generation of documentation from scratch
- No changes to the QA verdict format or QA process

## Stories

- 15-00-numbered-feature-folders (done)
- 15-01-code-doc-rule (done)
- 15-02-watermark-readme (done)
- 15-03-documenter-incremental (done)
- 15-04-dev-start-guard-marker (planned)
