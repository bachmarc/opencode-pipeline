# FEATURES.md — opencode-pipeline Dev Repo

Top-level index of features and their stories. Each feature has a directory under `docs/features/<name>/` with `feature.md` and `stories/` subdirectory.

| Feature | Title | Status | Owner | Stories | Traceability |
|---------|-------|--------|-------|---------|--------------|
| F-RETRO | Retroactive Traceability | done | — | RETRO-01, RETRO-02, RETRO-03, RETRO-04, RETRO-05 | REQ-002 |
| F-001 | Foundation | done | — | 01-03, 01-04, 01-05 | REQ-001, REQ-002, REQ-003, REQ-004, REQ-005 |
| F-002 | Internationalization (English) | done | — | 04-01, 04-02, 04-03, 04-04 | REQ-007, NFR-001 |
| F-003 | Documentation | done | — | 05-01 | REQ-008 |
| F-004 | Pipeline Evolution | planned | — | 06-01, 06-02, 06-03, 06-04, 06-05, 06-06, 06-07, 06-08, 06-09, 06-10, 06-11, 06-12, 06-13 | REQ-009, REQ-010, REQ-011, REQ-012, REQ-013 |

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
      feature.md          # scope, status, traceability (REQ-ID), claim info
      stories/
        <phase>-<id>-<slug>.md   # individual story (same format as before)
```

Each `feature.md` contains YAML-like header with fields: `id`, `title`, `status`, `owner`, `req`.
