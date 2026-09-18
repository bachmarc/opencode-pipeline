---
description: Implement a story isolated per Git branch (feature/<id>-<slug>) with cheap model — tests first, fake interfaces, developer targets only.
agent: developer
---

Implement story: $ARGUMENTS

- Expect story ID like `01-01`, `02-03` or `feature/01-01-slug`
- Use `scripts/resolve_story.py` to find the story and verify branch
- Use `scripts/intent.py` to track your progress
- Implement exactly the developer targets from your story file (found via resolve_story.py), tests first according to test criteria, use fakes
- Check `pytest` green, then use `scripts/prepare_commit_metadata.py` for commit message, then handoff to qa-manager

If $ARGUMENTS empty: list open stories from feature directories and ask which one.
