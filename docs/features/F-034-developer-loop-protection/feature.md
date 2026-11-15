---
id: F-034
title: Developer Loop Protection
status: planned
owner: ""
req: []
---

## Vision

Developer agent sessions are bounded: a step budget caps runaway loops,
item-wise spawn discipline limits restart loss to one unit of work, and
hard anti-loop rules in the developer prompt stop repetitive failing
actions before they consume an entire session.

## Context

VirtOffice session 2026-10-25 (story 26-09 E2E exploration, GLM-5.3-Flash
developer): a long-running exploration subagent looped chaotically;
together with server restarts the run needed 4 attempts. Token cost and
wall-clock loss from a single unbounded loop can exceed the cost of an
entire parallel wave. See also TODO.md → T-001.

## Stories

- 01-01-loop-protection-prompts (planned)
- 34-01-loop-protection-prompts (Planned)
