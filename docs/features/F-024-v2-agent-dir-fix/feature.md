---
id: F-024
title: V2 Agent Directory Fix
status: in-progress
owner: ""
req: []
---

## Vision

Agent Markdown files are discovered correctly by OpenCode V2 so that the Tab key
launches the architect (and all other custom agents) as expected.

## Context

OpenCode V2 changed the agent discovery directory from `agent/` (singular, V1)
to `agents/` (plural, V2). Because the live config clone still uses the old
`agent/` name, no custom agent is visible in V2 and pressing Tab to select the
architect has no effect. Additionally, the `temperature:` frontmatter field is a
deprecated V1 field — V2 ignores it and warns about it. Both issues need to be
fixed in the dev repo and deployed via the release branch.

## Stories

- 24-01-rename-agent-dir (in-progress)
