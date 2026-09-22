---
id: F-005
title: Documentation Model Reform
status: done
owner: ""
req: []
---

## Vision

When all stories of this feature are done, the pipeline's documentation model has
shifted from "architect-docs are primary, stories reference them" to "features and
stories are the primary source of truth, architect-docs are derived summaries."

Features become more than folders — they carry their own vision and context that
describes what all their stories together create. Stories become self-contained:
they carry their own purpose, requirements, and acceptance criteria without needing
to reference external REQ-IDs.

The Documenter's role expands: after implementation, it generates/updates
`requirements.md` and `design.md` as derived summaries with feature/story references,
serving as a quick-start for the Architect in the next session.

## Context

The current model has requirements.md and design.md as primary sources, with stories
referencing REQ-IDs. This creates problems:
- Stories are not self-contained (must read requirements.md to understand "why")
- In teams, everyone must write into central architect docs (bottleneck)
- The Architect must manually maintain requirements.md + design.md (duplication)
- Stories don't serve as project history (the "why" lives elsewhere)

The new model makes features/stories independently maintainable and uses the
Documenter to keep derived docs consistent.

## Stories

- 08-01-templates-reform (done) — Story + Feature templates with new sections
- 08-02-architect-prompt (done) — Architect prompt: features/stories as primary source
- 08-03-documenter-prompt (done) — Documenter prompt: generate summaries + consistency
