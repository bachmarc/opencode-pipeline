---
description: Implement a story isolated per Git branch (feature/<id>-<slug>) with cheap model — tests first, fake interfaces, developer targets only.
agent: developer
---

Implement story: $ARGUMENTS

- Expect story ID like `01-01`, `02-03` or `feature/01-01-slug`
- Create branch `feature/<story-id>-<slug>` (if not existing)
- Implement exactly the developer targets from `docs/stories/<id>.md`, tests first according to test criteria, use fakes
- Check `pytest` green, then handoff to qa-manager

If $ARGUMENTS empty: list open stories from STORIES.md and ask which one.
