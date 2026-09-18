---
description: Shows implementation status of all stories and errors — dialogue with QA manager per plan.
agent: qa-manager
---

Show status for: $ARGUMENTS

- Use `scripts/pipeline_status.py` to aggregate `STORIES.md`, `git branch -a`, latest commits, test suite/linter results, open QA FAILs/BLOCKEDs
- Answer in German compactly (table), then details for: $ARGUMENTS
- If $ARGUMENTS empty: overall status of all stories. If story ID/branch named: detail status + errors for this story.
