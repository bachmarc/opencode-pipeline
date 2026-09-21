# FEATURES.md — opencode-pipeline Dev Repo

Top-level index of features and their stories. Each feature has a directory under `docs/features/<name>/` with `feature.md` and `stories/` subdirectory.

| Feature | Title | Status | Owner | Stories |
|---------|-------|--------|-------|---------|
| F-RETRO | Retroactive Traceability | done | — | RETRO-01, RETRO-02, RETRO-03, RETRO-04, RETRO-05 |
| F-001 | Foundation | done | — | 01-03, 01-04, 01-05 |
| F-002 | Internationalization (English) | done | — | 04-01, 04-02, 04-03, 04-04 |
| F-003 | Documentation | in-progress | — | 05-01, 07-01, 07-02, 07-03 |
| F-004 | Pipeline Evolution | done | — | 06-01, 06-02, 06-03, 06-04, 06-05, 06-06, 06-07, 06-08, 06-09, 06-10, 06-11, 06-12, 06-13 |
| F-005 | Doc Model Reform | done | — | 08-01, 08-02, 08-03 |
| F-006 | Doc Model Migration | in-progress | — | 09-01, 09-02, 09-03, 09-04, 09-05, 09-06 |
| F-007 | Pipeline Enforcement Plugin | done | — | 11-01, 11-02, 11-03, 11-04, 11-05, 11-06, 11-07, 11-08 |
| F-008 | Polyglot QA Gate | planned | — | 12-01, 12-02, 12-03, 12-04, 12-05, 12-06, 12-07, 12-08, 12-09, 12-10 |
| F-009 | Project Migration | planned | — | 13-01, 13-02, 13-03, 13-04, 13-05, 13-06 |

## Feature status derivation

A feature's status is the minimum of its stories' statuses:
- All stories done → feature done
- Any story in-progress → feature in-progress
- Any story planned → feature not done

## Directory structure

```
docs/
  features/
    <feature-name>/
      feature.md          # Vision, Context, claim info
      stories/
        <phase>-<id>-<slug>.md   # individual story (same format as before)
```

Each `feature.md` contains YAML-like header with fields: `id`, `title`, `status`, `owner`.
