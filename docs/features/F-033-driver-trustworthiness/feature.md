---
id: F-033
title: Driver Trustworthiness (Status Booking Fixes)
status: planned
owner: ""
req: []
---

## Vision

`driver.py next` outputs only genuine actions — no noise from stale
status bookings. Every merged story carries a `Status: Done (merged as
<sha>)` line so the driver's status source reflects reality. A
booking-vs-git consistency check surfaces any story that is claimed done
but whose commit is not on main. Terminal states beyond `Done` and
`Planned` silence legitimate closed outcomes without driver noise.

## Context

VirtOffice session 2026-11-15 revealed that `driver.py` parsed ~36
actions of which only 2 were genuine — the rest were false positives from
story files never updated after merge. The merge flow updated STORIES.md
but not the story files (the driver's actual status source). A 49-file
manual true-up was required to restore driver usefulness. Full defect
analysis in `docs/reports/2026-11-15-virtoffice-status-booking-defects.md`
(D-1 through D-10). See also TODO.md → T-002.

## Stories

- 33-01-merge-status-update (Planned)
- 33-02-booking-check (Planned)
- 33-03-driver-status-vocabulary (Planned)
- 33-04-plan-check-status-guards (Planned)
