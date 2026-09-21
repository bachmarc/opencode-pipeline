---
id: F-009
title: Project Migration
status: planned
owner: ""
---

## Vision

Existing projects that were not started with the opencode pipeline can be seamlessly onboarded into the framework. A `/migrate-project` command triggers an interactive, LLM-guided migration dialogue that analyzes the project, builds a correct `AGENTS.md` from the template, creates missing infrastructure (`.pipeline/`, `qa_config.json`, directory structure), and optionally documents pre-pipeline work as retro stories. After migration, the project works with all pipeline features (worktrees, QA gate, session recovery, documenter) without manual setup.

## Context

The pipeline currently supports only greenfield projects via `scaffold_project.py`. But real-world adoption means onboarding existing projects — with their own `AGENTS.md` (possibly outdated or hand-written), `CLAUDE.md`, or no agent file at all. These projects have grown organically and contain a mix of project-specific knowledge and framework-level steering that may conflict with the current template.

A deterministic script cannot solve this: it requires understanding which parts of an existing `AGENTS.md` are project-specific (keep) vs. framework steering (replace with template). It requires dialogue with the user for ambiguous decisions (branch naming, retro story granularity, stack confirmation). This is an Architect task, delivered as a Command + Skill combination.

**Target audience:** Any developer with an existing project (Python, JS, Ruby, Java, Docker/mixed, or no recognizable stack) who wants to use the opencode pipeline for future development.

**Scope boundaries (what does NOT belong):**
- Automatic code refactoring (moving files into `src/core/` / `src/adapters/`)
- Automatic test generation or fake creation
- Changing the project's actual source code in any way
- CI/CD setup

## Stories

- 13-01-migrate-command (planned) — `/migrate-project` command + `migrate-project` skill scaffold
- 13-02-project-analyzer (planned) — Project analysis script (stack detection, structure scan, existing agent file parsing)
- 13-03-agents-md-generator (planned) — AGENTS.md generation: template + project-specific content via LLM dialogue
- 13-04-structure-provisioning (planned) — Missing directory/file provisioning (`.pipeline/`, `qa_config.json`, templates, `.gitignore`)
- 13-05-retro-story-generator (planned) — Optional retro story generation for pre-pipeline work
- 13-06-migration-validation (planned) — Post-migration validation (template constancy, structure completeness, qa_config)
