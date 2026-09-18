---
id: F-008
title: Polyglot QA Gate
status: done
owner: ""
req: []
---

## Vision

Any project — Ruby, JavaScript/TypeScript, Java (Gradle or Maven), HTML, JSON/YAML
config-heavy repos, and mixed-language monorepos — can pass the pipeline's QA gate.
The project declares its test stack once via a committed `qa_config.json`; portable
prompts and template sections contain NO concrete runner names (same abstraction
discipline as the model de-hardwiring).

## Context

`qa_compress.sh` hard-registers a single `pytest` checker with pytest-9-specific
output parsing. A Java/Ruby/JS project cannot pass the QA gate at all today.
Developer/QA/architect prompts and the constant sections of `templates/AGENTS.md`
name pytest explicitly, which leaks a project decision into the binding framework
interface. The user's daily work spans Ruby, JavaScript, Java, HTML, and JSON/YAML —
and real projects are mixed (e.g., Ruby + Java in one repo), so the config must be
a list of checkers run serially with AND semantics (all must be green).

Design decisions:

- **`qa_config.json`** in the project root, committed: `{"checkers": ["rspec", "gradle", "json"]}`.
  Missing file → default `["pytest"]` (backward compatible for all existing projects).
  Unknown checker name → loud FAIL. Empty list → explicit opt-out (data-only repos).
- **Checker plugins:** each runner/syntax check is one file in `scripts/qa_checkers/`
  that registers itself. Stories add files, no shared-file edits → parallel waves
  without merge conflicts.
- **python3 is a framework prerequisite** (not a project prerequisite): `qa_compress.sh`
  may use `python3 -c` for JSON parsing and stdlib-based syntax checks.
- **Testability via fake binaries:** every runner checker is tested with a stub
  executable on `PATH` that replays preserved output — no real runner needs to be
  installed in tests.
- **Architect onboarding duty:** when planning in a project without `qa_config.json`,
  the architect must retrofit one (stack-appropriate) — enforced via architect prompt.
- **Legacy projects:** `scripts/migrate_template_sections.py` lets the architect
  re-sync the constant sections of existing project AGENTS.md files after the
  template change — one command per project.

## Stories

- 12-01-qa-config-contract (done)
- 12-02-checker-rspec-jest (done)
- 12-03-checker-gradle-maven (done)
- 12-04-checker-json-yaml (done)
- 12-05-checker-html (done)
- 12-06-commit-metadata-polyglot (done)
- 12-07-prompt-genericization (done)
- 12-08-template-scaffold-config (done)
- 12-09-template-migration-tool (done)
- 12-10-check-architecture-polyglot (done)