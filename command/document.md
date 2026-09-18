---
description: Reconcile documentation against code changes — run git diff, check docs consistency, update README/design/docstrings. Triggered manually or after QA-PASS.
agent: documenter
---

Reconcile documentation for: $ARGUMENTS

- IF $ARGUMENTS empty: reconcile docs for current feature branch (git diff against main)
- IF $ARGUMENTS is story-id (e.g., `06-10`) or feature-name: reconcile docs for that branch
- Run git diff against main, read affected files + docs/, check consistency
- Update README, design.md, docstrings, remove stale comments
- Commit documentation changes on the same branch
- Report what was updated (compact summary)
