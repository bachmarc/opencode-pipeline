# FEATURES.md — opencode-pipeline Dev Repo

Top-level index of features and their stories. Each feature has a directory under `docs/features/F-<ID>-<name>/` with `feature.md` and `stories/` subdirectory.

| Feature | Title | Status | Owner | Stories |
|---------|-------|--------|-------|---------|
| F-RETRO | Retroactive Traceability | done | — | RETRO-01, RETRO-02, RETRO-03, RETRO-04, RETRO-05 |
| F-001 | Foundation | done | — | 01-03, 01-04, 01-05 |
| F-002 | Internationalization (English) | done | — | 04-01, 04-02, 04-03, 04-04 |
| F-003 | Documentation | done | — | 05-01, 07-01, 07-02, 07-03 |
| F-004 | Pipeline Evolution | done | — | 06-01, 06-02, 06-03, 06-04, 06-05, 06-06, 06-07, 06-08, 06-09, 06-10, 06-11, 06-12, 06-13 |
| F-005 | Doc Model Reform | done | — | 08-01, 08-02, 08-03 |
| F-006 | Doc Model Migration | done | — | 09-01, 09-02, 09-03, 09-04, 09-05, 09-06 |
| F-007 | Pipeline Enforcement Plugin | done | — | 11-01, 11-02, 11-03, 11-04, 11-05, 11-06, 11-07, 11-08 |
| F-008 | Polyglot QA Gate | done | — | 12-01, 12-02, 12-03, 12-04, 12-05, 12-06, 12-07, 12-08, 12-09, 12-10, 12-11, 12-12 |
| F-009 | Project Migration | done | — | 13-01, 13-02, 13-03, 13-04, 13-05, 13-06 |
| F-010 | Eliminate Derived Docs | done | — | 14-01 |
| F-011 | Living Code Documentation | done | — | 15-00, 15-01, 15-02, 15-03, 15-04 |
| F-012 | Clarification Markers | done | — | 16-01 |
| F-013 | Framework Path Consolidation | done | — | 17-01, 17-02, 17-03, 17-04, 17-05 |
| F-014 | Architecture Checker Evolution | planned | — | 18-01 |
| F-019 | Python QA Toolchain | done | — | 19-01, 19-02 |
| F-020 | Script Portability Fixes | done | — | 20-01, 20-02, 20-03 |
| F-021 | Documenter Scope Fix | done | — | 21-01, 21-02 |
| F-022 | QA Compress Fast Mode | done | — | 22-01, 22-02 |

## Feature status derivation

A feature's status is the minimum of its stories' statuses:
- All stories done → feature done
- Any story in-progress → feature in-progress
- Any story planned → feature not done

## Directory structure

```
docs/
  features/
    F-<ID>-<feature-name>/
      feature.md          # Vision, Context, claim info
      stories/
        <phase>-<id>-<slug>.md   # individual story (same format as before)
```

Each `feature.md` contains YAML-like header with fields: `id`, `title`, `status`, `owner`.
