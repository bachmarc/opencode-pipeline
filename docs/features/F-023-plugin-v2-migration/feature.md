---
id: F-023
title: Plugin V2 Migration
status: planned
owner: ""
req: []
---

## Vision

`pipeline-enforcement.ts` loads successfully in OpenCode V2, all six pipeline guards are active
on every session, and no plugin-related warnings appear in the server log at startup.

## Context

OpenCode was upgraded from V1 to V2. The V2 runtime no longer executes V1-style plugin
implementations — it requires a `default` export built with `Plugin.define({ id, setup })` from
the `@opencode/plugin` package (note: no `-ai` suffix). `pipeline-enforcement.ts` was written
for V1 and fails silently at startup with `SchemaError(Missing key at ["default"])`.

As long as it fails to load, all six pipeline guards (merge, dev-start, architect-code,
story-status, session-recovery, documenter) are inactive — the pipeline's process safety
is broken.

`rtk.ts` has the same V1 issue but is a personal tool plugin unrelated to the framework;
it is maintained separately outside this repo.

## Stories

- 23-01-migrate-pipeline-enforcement (planned)
