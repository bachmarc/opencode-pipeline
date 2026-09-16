---
description: Kompakter QA-Testreport — führt pytest aus und liefert nur Exit-Code, Fehler-/Testnamen und Assertions (komprimiert, keine Log-Spam). Für qa-manager und User.
---

Führe den QA-Testsummary aus und gib das Ergebnis kompakt weiter.

1. Führe das Kompressions-Skript aus und prüfe den Exit-Code:
   `~/.config/opencode/scripts/qa_compress.sh`
2. Falls das Skript nicht ausführbar ist, mache es ausführbar:
   `chmod +x ~/.config/opencode/scripts/qa_compress.sh`
3. Reiche das komprimierte Ergebnis exakt so weiter (1:1, nicht umformulieren).
   Ergänze NUR einen kurzen Status-Kopf:

   - `exit_code = 0` → Status: **PASS** (Tests grün).
   - `exit_code != 0` → Status: **FAIL**, `failed_tests` = die Liste aus dem Skript.

Keine vollständigen Logs, keine Tracebacks, kein Wiederkäuen. Nur die kompakte Ausgabe.
