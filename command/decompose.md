---
description: Decompose Requirements into Features & Stories (STORIES.md + docs/features/*/stories/) — cut so that cheap mass models (configured locally via agent.developer.model) can implement them per branch.
agent: architect
---

Decompose into features and stories based on user requirements: $ARGUMENTS

- Create feature files (`docs/features/<name>/feature.md`) with vision + context
- Create `STORIES.md` (phase index like vocabulary) + `docs/features/<name>/stories/<phase>-<id>-<slug>.md` per story with context, requirements, developer targets, acceptance and test criteria
- Use `scripts/create_story.py` to generate story files from template
- Cut stories so that the locally configured cheap mass model (`agent.developer.model`) can implement them isolated per feature/<id>-<slug> branch
- Test criteria must be fulfillable BEFORE implementation (fakes!)

If $ARGUMENTS empty: use current project in cwd.
