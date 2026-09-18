---
id: F-006
title: Documentation Model Migration
status: planned
owner: ""
---

## Vision

When all stories are done, the entire repo consistently uses the new documentation
model: features and stories are the primary source of truth, requirements.md and
design.md are Documenter-generated summaries, and all tooling (scripts, commands,
templates, agent prompts) references the new model. No REQ-IDs remain as primary
anchors — feature/story references replace them everywhere.

## Context

Feature F-005 (doc-model-reform) established the new documentation model: new
templates, updated architect and documenter prompts. But the existing repo data
(22 story files, 5 feature.md files, STORIES.md, FEATURES.md, requirements.md,
design.md) plus supporting files (commands, QA-manager prompt, developer prompt,
AGENTS.md template, scripts, tests) still use the old REQ-ID/Design-§ model.

This feature migrates everything to the new model in a controlled sequence.

## Stories

- 09-01-migrate-features (planned) — Migrate 5 feature.md files to new format (Vision + Context, drop req: field)
- 09-02-migrate-stories (planned) — Migrate 22 story files to new 5-section format (Feature: instead of Traceability:)
- 09-03-migrate-indexes (planned) — Migrate STORIES.md + FEATURES.md to feature-references
- 09-04-migrate-summaries (planned) — Rewrite requirements.md + design.md as Documenter-style summaries
- 09-05-migrate-prompts-commands (planned) — Update QA-manager, developer prompts + commands + AGENTS.md template
- 09-06-migrate-scripts-tests (planned) — Update scripts + tests that reference REQ-IDs
