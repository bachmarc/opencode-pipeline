---
description: QA gate for feature branch — checks requirements, tests, architecture separation, fake interfaces. Returns PASS/FAIL/BLOCKED. Also status dialogue per plan.
agent: qa-manager
---

Check QA gate / status for: $ARGUMENTS

- IF $ARGUMENTS empty and implementation running: act as status dialogue partner — summarize: `STORIES.md` status, all `feature/*` branches, latest `pytest` logs, open FAILs/BLOCKEDs (table story|branch|tests|qa|error) and answer user question about status/errors
- IF $ARGUMENTS branch `feature/<id>-<slug>` or story ID: check QA gate against `docs/requirements.md` + story acceptance criteria, execute `pytest`/`ruff`/`mypy`, verify function vs connectivity + fakes → PASS/FAIL/BLOCKED
- On FAIL automatically spawn `developer` fix on same branch (loop), on BLOCKED escalate precise question to user
