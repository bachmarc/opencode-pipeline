---
id: F-026
title: Codebase Snapshot in Stories
status: planned
owner: ""
req: []
---

## Vision

Every story file contains a `## Codebase Snapshot` section written by the Architect at decomposition time. The Developer reads it as the first step and starts implementing immediately — no redundant codebase exploration needed.

## Context

When the Architect decomposes a feature into stories, they already explore the relevant parts of the codebase: which files are affected, which functions exist, which tests are already there. This knowledge currently lives only in the Architect's session context and is lost by the time the Developer starts.

The Developer then re-explores the same codebase from scratch — reading the same files, running the same greps — before they can start writing tests. This is pure duplication: the Architect paid for the exploration, the Developer pays again.

The fix is simple: the Architect writes down what they found as part of the story. The `## Codebase Snapshot` section is not a design document — it is a navigation aid. It tells the Developer exactly where to look: which files are touched, which functions are entry points, which tests already exist for adjacent code. Optional by convention (Trivial one-liners don't need it), mandatory by habit for anything touching existing code.

## Stories

- 26-01 codebase-snapshot-in-story-template (planned)
