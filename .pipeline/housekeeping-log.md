# Housekeeping Log

Architect-direct code fixes. Each entry: date, story context, file, change, user authorization.

---

## 2026-11-15 — 33-05 merge_if_passed ordering fix

- **File:** `scripts/merge_if_passed.py`
- **Change:** Move status-update block (L424-432) from after `run_post_merge_suite()` to before it.
- **Reason:** 3-line reorder, no logic change. Post-merge suite causes SIGTERM before status update runs.
- **Story:** 33-05 (planned but trivial — user authorized direct fix)
- **Authorization:** User: "3 zeilen gehen einfach so hier"

---

## 2026-11-21 — Stray conflict marker in README.md

**File:** `README.md` line 477
**Symptom:** Conflict block between HEAD and `feature/27-02-js-ts-lint-checkers` left unresolved
in the file — pre-existing artifact on origin/main, undetected because README.md is free-edit
(no QA checker scans it for markers).
**Fix:** Kept HEAD version ("one inline function in `scripts/qa_compress.py` + one entry in the
`CHECKERS` dict"). Remote version was an earlier, less specific draft.
**Risk:** None — prose-only change in README, no logic.

**File:** `skills/migrate-project.md` line 129
**Symptom:** Literal `<<<<<<< HEAD` line in Phase 5 of the migrate-project skill, deployed
to live-clone via release branch. No matching `=======` or `>>>>>>>` — stray artifact.
**Root cause:** Commit `0b4a264` (merge 25-02, manual conflict resolution) accidentally
kept the `<<<<<<< HEAD` opener without the rest of the conflict block.
**Fix:** Deleted the single stray line. Content below it is the intended Phase 5 content.
**Risk:** None — cosmetic line removal in a prompt skill file, no logic change.
