---
id: F-037
title: Eliminate STORIES.md
status: planned
owner: ""
req: []
---

## Vision

STORIES.md is eliminated. Story files are the single source of truth for
story status and content. Feature files are the single source of truth for
phase narrative and context. No manually maintained index that drifts from
reality. The same principle as F-010 (requirements.md + design.md
eliminated) — applied to the stories index.

## Context

STORIES.md is a manually maintained aggregate that duplicates what already
lives in story files (status, criteria) and feature.md files (narrative,
context). The driver already reads story files, not STORIES.md. The
VirtOffice incident (T-002, D-1) was a symptom: 49 story files diverged
from STORIES.md, causing ~34 false driver actions. F-033 (story 33-01)
fixes the divergence by writing `Status: Done` atomically on merge. F-037
removes the secondary source entirely: once story files are the reliable
truth, STORIES.md is redundant by design.

Three change areas:
- **Scripts** that read STORIES.md must switch to story files.
- **Plugins** that check STORIES.md updates become obsolete or need updating.
- **STORIES.md** itself is deleted.

## Stories

- 37-01-feature-md-stories-list-accuracy (Planned)
- 37-02-script-stories-md-removal (Planned)
- 37-03-plugin-prompt-stories-md-deletion (Planned)
