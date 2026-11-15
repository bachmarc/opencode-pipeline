---
id: F-036
title: QA as Test Oracle
status: planned
owner: ""
req: []
---

## Vision

The QA-Manager is a genuine test oracle, not a rubber stamp. It independently
reviews the developer's tests against the story spec, adds missing coverage in
the project's own test idiom (pytest, Playwright, Jest, RSpec — derived from
repo context), and only then validates. A developer can no longer "write tests
that confirm wrong assumptions" and have them pass the QA gate unnoticed.

## Context

Today's QA gate runs the developer's tests and checks if they are green. If
the developer baked a wrong assumption into both the implementation and the
tests, QA confirms the wrong behavior as correct — a circular, self-sealing
loop. The fix: QA independently evaluates the tests against the story spec
(Test Criteria section), augments or corrects them where gaps exist (using
the project's test conventions), commits the additions, and then validates
the full suite. Forcing "unit tests only" is explicitly avoided — the right
test type (unit / integration / E2E / Playwright) is derived from the repo's
declared test strategy and existing patterns.

## Stories

- 36-01-qa-test-review-and-augmentation (Planned)
