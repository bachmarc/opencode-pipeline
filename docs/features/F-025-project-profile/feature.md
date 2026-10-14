---
id: F-025
title: Project Profile & QA Configuration
status: planned
owner: ""
req: []
---

## Vision

When a project is onboarded via `/migrate`, the pipeline knows exactly how to build, test, and deploy it — without guessing. `qa_compress.py` runs the right test command for any language. The Architect can always offer deployment options because they are documented. Existing project history is preserved as done stories, a baseline, or consciously discarded — never silently lost.

## Context

The pipeline is used in two modes: self-development (dogfooding) and building external User-Projects. In self-development mode, `qa_compress.py` runs pytest and checks pipeline invariants. In User-Project mode, the pipeline needs to adapt: Ruby projects use rspec, Go projects use `go test`, TypeScript projects use jest — and every project deploys differently.

Today, `/migrate` detects the tech stack but never asks about the test command or deployment strategy. `provision_structure.py` creates directories but never writes `qa_config.json`. `analyze_project.py` detects stack markers but not test commands or deploy hints. The result: migrated projects get incomplete pipeline configurations, `qa_compress.py` defaults to pytest (wrong for most projects), and the Architect never has deployment context to offer.

A second gap is project history. Old projects arrive with their development story embedded in git commits, a CHANGELOG, TODO notes, or just README history. The pipeline currently offers retro stories but never asks the user how they want to handle existing history — granular stories, a single baseline, or a clean start.

Three scripts need extension (`analyze_project.py`, `provision_structure.py`, `create_retro_stories.py`), the migrate skill needs two new dialog phases (test+deploy config, history handling), and `validate_migration.py` needs two new checks.

## Stories

- 25-01 analyze-project-profile (planned)
- 25-02 migrate-dialog-and-qa-config (planned)
- 25-03 history-dialog (planned)
