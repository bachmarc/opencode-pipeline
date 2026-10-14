---
id: F-023
title: Plugin V2 Migration
status: planned
owner: ""
req: []
---

## Vision

Both global plugins (`pipeline-enforcement.ts` and `rtk.ts`) load successfully in OpenCode V2,
their guards and token-saving hooks are active on every session, and no plugin-related warnings
appear in the server log at startup.

## Context

OpenCode was upgraded from V1 to V2. The V2 runtime no longer executes V1-style plugin
implementations — it requires a `default` export built with `Plugin.define({ id, setup })` from
the `@opencode/plugin` package (note: no `-ai` suffix). Both plugins were written for V1 and
fail silently at startup with `SchemaError(Missing key at ["default"])`.

As long as they fail to load:
- All six pipeline-enforcement guards (merge, dev-start, architect-code, story-status,
  session-recovery, documenter) are not enforced — the pipeline's process safety is broken.
- The rtk token-saving rewrite is inactive — every bash command goes to the model unrewritten.

The two plugins are independent of each other and can be migrated in parallel.

## Stories

- 23-01-migrate-pipeline-enforcement (planned)
- 23-02-migrate-rtk (planned)
