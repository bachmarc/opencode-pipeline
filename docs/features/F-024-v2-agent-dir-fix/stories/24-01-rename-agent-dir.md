# Story 24-01 — Rename agent/ to agents/ and remove deprecated temperature frontmatter

Status: Done
Feature: V2 Agent Directory Fix (F-024)

## Context / Purpose

OpenCode V2 changed the agent Markdown discovery path from `agent/` (V1) to
`agents/` (V2, plural). Because the live config clone (`~/.config/opencode`)
still ships the old `agent/` directory, OpenCode V2 never discovers the custom
pipeline agents (architect, developer, qa-manager, documenter). The result:
pressing Tab to open the architect dialog does nothing.

Additionally, all four agent Markdown files carry a `temperature:` frontmatter
field that is explicitly deprecated in V2 (listed in the docs as a legacy V1
field). V2 ignores this silently.

Both issues live in the dev repo (`~/Development/opencode-pipeline`) and are
deployed to the live config clone via the `release` branch.

## Requirements

1. The agent Markdown directory is named `agents/` (plural) in the repo.
2. No agent Markdown file contains a `temperature:` frontmatter field.
3. `opencode.json` retains `agent.*.model` and `agent.*.reasoningEffort` entries
   (these are still valid V2 `opencode.json` fields and do not move).
4. All existing content (description, mode, system prompt body) is preserved
   unchanged in the four agent files.
5. The old `agent/` directory no longer exists in the repo.

## Developer Targets (exactly, no more / no less)

- Rename `agent/` → `agents/` (git mv all four files, remove old dir).
- In each of the four files (`architect.md`, `developer.md`, `qa-manager.md`,
  `documenter.md`): delete the `temperature: ...` line from the YAML frontmatter.
- No other changes — body text, description, mode stay identical.
- Update module header comment in this story file to reflect Done status after
  implementation (i.e., set Status to Done before commit).

## Acceptance criteria (checked by qa-manager)

- `agent/` directory does NOT exist in the repo.
- `agents/` directory DOES exist and contains exactly the four files:
  `architect.md`, `developer.md`, `qa-manager.md`, `documenter.md`.
- None of the four files contains a `temperature:` line in their frontmatter.
- Each file still has `description:` and `mode:` frontmatter fields.
- `opencode.json` is unchanged (agent model entries remain under `agent.*`).
- `pytest` passes (existing framework checks are not broken).

## Test criteria (must exist BEFORE implementation)

File: `tests/test_v2_agent_dir.py`

- `test_agents_dir_exists`: `agents/` directory exists relative to repo root.
- `test_agent_dir_gone`: `agent/` directory does NOT exist relative to repo root.
- `test_four_agent_files`: `agents/` contains exactly `architect.md`,
  `developer.md`, `qa-manager.md`, `documenter.md` (no more, no less).
- `test_no_temperature_in_frontmatter`: for each of the four files, parse YAML
  frontmatter and assert `temperature` key is absent.
- `test_description_and_mode_present`: for each of the four files, assert
  `description` and `mode` keys are present in frontmatter.
