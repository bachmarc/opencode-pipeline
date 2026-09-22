---
id: F-012
title: Clarification Markers
status: planned
owner: ""
req: []
---

## Vision

When all stories of this feature are done, the pipeline has a formal mechanism to prevent
ungeklärte Annahmen from leaking into implementation. Story templates require explicit
`[NEEDS CLARIFICATION: ...]` markers for anything ambiguous, the architect uses them during
story creation, the user resolves them at the review checkpoint, and QA verifies none remain
before PASS. This closes the gap between "architect guessed" and "user decided."

## Context

Inspired by spec-kit's clarification pattern: when an LLM writes specifications, it tends to
make plausible but potentially wrong assumptions instead of flagging uncertainty. Our pipeline
already has an informal clarify-step (architect asks user), but nothing prevents a story from
reaching the developer with unresolved ambiguities baked in as silent assumptions.

Adding `[NEEDS CLARIFICATION]` markers is a lightweight, template-level change that makes
uncertainty visible and verifiable — no new scripts or plugins required.

## Stories

- 16-01-clarification-markers (planned)
