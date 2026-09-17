---
description: Compact QA test report — runs pytest and delivers only exit code, error/test names and assertions (compressed, no log spam). For qa-manager and user.
---

Execute the QA test summary and pass the result compactly.

1. Execute the compression script and check the exit code:
   `~/.config/opencode/scripts/qa_compress.sh`
2. If the script is not executable, make it executable:
   `chmod +x ~/.config/opencode/scripts/qa_compress.sh`
3. Pass the compressed result exactly as is (1:1, do not rephrase).
   Add ONLY a short status header:

   - `exit_code = 0` → Status: **PASS** (tests green).
   - `exit_code != 0` → Status: **FAIL**, `failed_tests` = the list from the script.

No full logs, no tracebacks, no regurgitation. Only the compact output.
