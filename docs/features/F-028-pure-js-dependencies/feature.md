---
id: F-028
title: Pure-JS Dependency Preference
status: planned
owner: ""
req: []
---

## Vision

When an Architect designs a Node.js/TypeScript project, they default to pure-JavaScript
(or pure-TypeScript) npm packages over native-addon alternatives. This avoids
build-time compilation failures (`node-gyp`, `binding.gyp`) and runtime incompatibilities
between Node.js versions and native binary formats — especially in Docker containers,
CI environments, and across developer machines with different platforms.

## Context

**Root cause (VirtOffice incident, extended):** Beyond the ESLint/TypeScript version
mismatches, a recurring class of problems in Node.js projects involves native addons:
packages like `bcrypt`, `argon2`, `sharp`, `sqlite3`, `canvas` require native compilation
at install time (`node-gyp`). On mismatched Node.js versions or in minimal Docker images
(missing `python`, `make`, `gcc`), this silently fails or produces hard-to-debug errors.

Pure-JS alternatives exist for most common cases:
- `bcrypt` → `bcryptjs` (pure JS, same API)
- `argon2` (native) → `@node-rs/argon2` or keep but document build req
- `sqlite3` → `better-sqlite3` (still native) or `@sqlite.org/sqlite-wasm` (WASM)
- `sharp` → no pure-JS equivalent, but must document libvips requirement

The Architect prompt should encode this as a standing recommendation: when proposing
dependencies in scaffold stories, prefer pure-JS alternatives and explicitly flag
native addons with their build requirements.

## Stories

- 28-01 architect-pure-js-preference (planned) — architect.md gets dependency guidance
