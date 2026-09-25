---
id: F-019
title: Python QA Toolchain
status: planned
owner: ""
req: []
---

## Vision

The entire framework toolchain runs on any platform (Windows, Linux, macOS) without requiring
bash or any shell other than Python. `qa_compress.py` replaces `qa_compress.sh` as the sole
QA entry point. All 8 checker plugins are Python modules. The test suite runs fully green on
Windows — no skipped tests, no `/bin/bash` errors. Session recovery pulls automatically on
every session start.

## Context

Two problems surfaced after Feature 17 (Framework Path Consolidation):

1. **`qa_compress.sh` is the only bash file in an otherwise all-Python framework.** All other
   scripts (`session_recovery.py`, `merge_if_passed.py`, `worktree_setup.py`, …) are Python.
   The 8 checker plugins (`qa_checkers/*.sh`) are also bash. On Windows, `bash` is not in
   PATH → 26 of 354 tests fail with `/bin/bash: … No such file or directory`. The tests are
   not broken — the platform is incompatible with bash.

2. **`session_recovery.py` does not pull before scanning.** The AGENTS.md rule "pull before
   work" is documented but not enforced by the script itself. A developer who forgets the
   manual `git pull` gets a stale state scan. The script already has `run_git_command()` —
   adding the pull is a three-line change.

**Target audience:** Any developer running the pipeline on Windows (or any platform without
bash). Also benefits Linux/macOS users by making the toolchain uniform.

**Scope boundaries (what does NOT belong):**
- Changing the QA output format (must remain identical to current `qa_compress.sh` output)
- Adding new checkers
- Changing `qa_config.json` contract
- Changing how `prepare_commit_metadata.py` works (it reads `qa_config.json` independently)

## Architecture

**`qa_compress.py` — same contract as `qa_compress.sh`:**
- Registry pattern: `CHECKERS: dict[str, Callable[[], tuple[str, int]]]`
- Checker discovery: import all `scripts/qa_checkers/*.py` modules at startup (same as
  bash `source` loop)
- Each checker module calls `register_check(name, fn)` on import (self-registering)
- `qa_config.json` parsing: already Python in the `.sh` — identical logic
- Output format: identical to current bash output (`# QA-Testsummary`, `## <name> (exit: N)`,
  `overall: PASS/FAIL`)
- Exit code: 0 = PASS, 1 = FAIL (identical)

**Checker modules `scripts/qa_checkers/<name>.py`:**
- Each module defines one function and calls `register_check(name, fn)` at module level
- Checker function: runs external tool via `subprocess.run()`, parses output with `re`,
  returns `(compressed_output: str, exit_code: int)`
- Fake runners in tests: Python scripts (`sys.stdout.write(output); sys.exit(code)`) instead
  of bash heredoc scripts — platform-independent

**`session_recovery.py` — `git pull` at startup:**
- `run_git_command(["pull"], repo_path)` called at the start of `main()`, before
  `collect_state()`
- Output printed to stderr (same channel as the summary)
- Pull failure is non-fatal: print warning, continue with state collection

## Stories

- 19-01-qa-compress-python (planned) — qa_compress.py + 8 Python checker modules, bash files deleted
- 19-02-session-recovery-pull (planned) — git pull in session_recovery.py + test_resolve_by_id fix
