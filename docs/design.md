# Design — opencode-pipeline Dev Repo

**Status:** Draft for review · Traceability: REQ-IDs referenced per section.

## 1. Two-clone topology (REQ-001, REQ-005)

```
github.com:bachmarc/opencode-pipeline.git
        │
        ├── /mnt/content_main/Development/opencode-pipeline   DEV clone
        │     - full pipeline workflow: stories, branches, worktrees, QA gate
        │     - pytest self-checks run here
        │
        └── ~/.config/opencode                                 LIVE clone
              - read-only: git pull (main, after QA-PASS merges) + opencode restart
              - gitignored local state stays untouched: opencode.jsonc, cron.db
```

Deployment is manual and staged: after a QA-PASS merge to `main`, the user pulls in the
live clone and restarts opencode. The live clone's working tree must never be edited.

## 2. Retro traceability (REQ-002)

`STORIES.md` carries a phase `Retro` with one entry per already-made direct change
(model de-hardwiring, role abstraction, permission.task doc, AGENTS.md template, README).
Each entry links the commit hash. Status `Retro-Erledigt` — these are documentation, not
re-implementation targets.

## 3. Self-check architecture (REQ-003, REQ-004)

This repo's "product" is configuration; its invariants are checkable by reading itself:

- **`tests/test_framework.py`** — pytest, stdlib only. Checks:
  1. `agent/*.md` frontmatter: parseable YAML block, no `model:` key (models live in the
     local `opencode.jsonc` only), required keys present (`description`, `mode`).
  2. No concrete model/provider names in portable files (`agent/`, `command/`, `skills/`,
     `templates/`, `scripts/`): regex over known patterns (e.g. `glm-`, `deepseek`,
     `qwen`, `haiku`, `claude-`, `ollama-docker`, `:cloud`), with an explicit allowlist for
     legitimate references (e.g. `CLAUDE.md` filename mentions).
  3. `templates/AGENTS.md` exists and contains the constant section markers (Workflow,
     Git conventions, Languages, Prohibitions) plus `<...>` placeholders.
  4. `scripts/qa_compress.sh` passes `bash -n` (syntax) and has the exec bit.
- **Fake perspective:** The only "external dependency" is the file system — pytest tmp_path
  and the repo files themselves. No fakes needed; checks are pure and deterministic.
- **QA integration:** `pytest tests/` output is compressed by `qa_compress.sh` as usual —
  the QA gate now has a deterministic target for this repo.

## 4. Deploy procedure (REQ-005)

Documented in README (§ Deployment): `git pull` in `~/.config/opencode` + restart of
opencode (config is loaded once at startup). Optional convenience later; manual is the
default. The local `opencode.jsonc`/`cron.db` are gitignored and survive pulls untouched.

## 5. Template constancy (REQ-006)

`templates/AGENTS.md` sections Workflow / Git conventions / Languages / Prohibitions are
the binding interface. The self-check (§3, check 3) asserts their presence so accidental
deletion or restructuring fails QA.

## 6. Versioning

`APP_VERSION = "0.1.0"` in `APP_VERSION.py` at repo root; bump on notable merges
(documented in STORIES.md). Traceability anchor for releases.

## 7. Decisions

| # | Decision | Reason |
|---|---|---|
| D1 | No CI yet | local pytest + QA gate is the contract; CI later |
| D2 | Live clone stays manual | the framework steers the running agent — staged rollout beats automation |
| D3 | English repo docs, German prompts | portable repo vs. dialogue-facing prompts |
| D4 | Self-checks read the repo only | zero infra, deterministic, cheap-model-evaluable |