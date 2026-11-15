# Housekeeping Log

Architect-direct code fixes. Each entry: date, story context, file, change, user authorization.

---

## 2026-11-15 — 33-05 merge_if_passed ordering fix

- **File:** `scripts/merge_if_passed.py`
- **Change:** Move status-update block (L424-432) from after `run_post_merge_suite()` to before it.
- **Reason:** 3-line reorder, no logic change. Post-merge suite causes SIGTERM before status update runs.
- **Story:** 33-05 (planned but trivial — user authorized direct fix)
- **Authorization:** User: "3 zeilen gehen einfach so hier"
