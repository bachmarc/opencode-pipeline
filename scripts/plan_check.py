#!/usr/bin/env python3
"""plan_check.py — deterministic planning QA for story files (Story 30-05).

Scans ``docs/features/*/stories/*.md`` and reports planning defects that weak
planner models introduce mechanically. No LLM, no guessing: purely textual
rules, stdlib only.

Scope:
  - Only OPEN stories are checked (``Status:`` line value not starting with
    "Done"). Done stories are historical record and are never flagged.
  - ``--story <file>`` checks a single story file. The create-target universe
    and the conflict candidates are still computed from ALL open stories under
    the root, because sequenced references and same-file conflicts are
    cross-story findings by definition.

Checks (problem kinds):
  1. ghost-reference (FAIL): a backticked repo path (contains "/" or ends with
     a file suffix) referenced as EXISTING — an extend/existing verb before
     the token, or "existing" as one of the first two words after it — that
     does not exist in the repo and is not a create-target of any open story.
  2. sequenced-reference (WARN): an extend/existing path that does not exist
     YET but is a create-target of ANOTHER open story — deliberate sequencing
     (real case: 30-02 extends scripts/driver.py, which open 30-01 creates).
     Exit code unchanged. Create-class mentions of such paths ("created by
     <story>") are reported the same way.
  3. clarification-marker (FAIL): any "[NEEDS CLARIFICATION" marker in an open
     story outside backticks (the acceptance-criteria boilerplate mention
     "`[NEEDS CLARIFICATION]`" is backticked and therefore not a marker).
     Markers are resolved at the planning checkpoint, never carried into dev.
  4. missing-section (FAIL): a required section absent or empty:
     Context / Purpose, Requirements, Developer Targets, Acceptance criteria,
     Test criteria. (Heading prefixes match, e.g. "Acceptance criteria
     (checked by qa-manager)" satisfies "Acceptance criteria".)

Conflict candidates (WARN, separate JSON list, exit code unaffected): files
mentioned in Developer Targets target lines ("-" lines) by more than one OPEN
story. The architect resolves them by declaring sequential waves in the
STORIES.md phase block; the script does not guess ordering.

Verb heuristic (textual, deterministic):
  - create verbs: create/creates/created, add/adds/added,
    introduce/introduces/introduced — the path is a deliverable, exempt from
    existence checks (it is being created, not referenced as existing).
  - extend/existing verbs: extend/extends/extended, existing/exists/exist —
    the path is referenced as already present, so it must exist.
  - Verb lookup: the text BEFORE the token on the same line (any position),
    else the first two words AFTER the token (the "- `path` — existing ..."
    snapshot idiom). The after-lookup only applies to tokens containing "/"
    (real repo paths); suffix-only name mentions (e.g. "`process.json`
    exists.") stay unclassified. Tokens that are globs ("*"), contain
    whitespace, angle brackets, or are directory mentions (trailing "/")
    are never checked.

JSON contract (stdout):
  {"result": "PASS" | "FAIL",
   "problems": [{"story": "<id>", "kind": "<kind>", "detail": "..."}],
   "conflict_candidates": [{"file": "<path>", "stories": ["<id>", ...]}]}

Exit codes:
  0 - PASS (no FAIL-kind problems; WARN entries and conflict candidates allowed)
  1 - FAIL (at least one ghost-reference / clarification-marker /
      missing-section problem)
  2 - usage error (--root/--story path not found)
"""

import argparse
import json
import re
import sys
from pathlib import Path

# --- textual rules -----------------------------------------------------------

CREATE_VERBS = {"create", "creates", "created", "add", "adds", "added",
                "introduce", "introduces", "introduced"}
EXIST_VERBS = {"extend", "extends", "extended", "existing", "exists", "exist"}

# A required section matches a heading whose normalized text starts with the
# entry (real headings carry suffixes like "(checked by qa-manager)").
REQUIRED_SECTIONS = [
    ("context / purpose", "Context / Purpose"),
    ("requirements", "Requirements"),
    ("developer targets", "Developer Targets"),
    ("acceptance criteria", "Acceptance criteria"),
    ("test criteria", "Test criteria"),
]

# Sections scanned for ghost/sequenced references (all body lines incl.
# continuations; Developer Targets target lines additionally feed the
# conflict/touched sets).
SCAN_SECTIONS = ["codebase snapshot", "developer targets"]

FAIL_KINDS = {"ghost-reference", "clarification-marker", "missing-section"}

BACKTICK_RE = re.compile(r"`([^`\n]+)`")
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
STATUS_RE = re.compile(r"^Status:\s*(.*)$")
STORY_ID_RE = re.compile(r"^(\d+-\d+)")


def _repo_root() -> Path:
    """Repo root for existence checks: nearest .git upward from cwd, else cwd."""
    cwd = Path.cwd()
    for candidate in (cwd, *cwd.parents):
        if (candidate / ".git").exists():
            return candidate
    return cwd


def _is_path_token(token: str) -> bool:
    """True if the backticked token resolves to a repo path (not prose/glob/CLI)."""
    if "*" in token or " " in token or "<" in token or ">" in token:
        return False
    if "/" in token:
        return not token.endswith("/")
    return re.search(r"\.[A-Za-z][A-Za-z0-9]{0,7}$", token) is not None


def _words(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def _classify(before: str, after: str, token: str) -> str | None:
    """Classify a token occurrence: "create", "extend" (must exist), or None."""
    before_words = set(_words(before))
    if before_words & CREATE_VERBS:
        return "create"
    if before_words & EXIST_VERBS:
        return "extend"
    # The "- `path` — existing ..." snapshot idiom: the verb follows the token.
    # Only for real repo-path tokens (contain "/"); suffix-only name mentions
    # (e.g. `process.json` exists.) stay unclassified.
    if "/" in token:
        for word in _words(after)[:2]:
            if word in CREATE_VERBS:
                return "create"
            if word in EXIST_VERBS:
                return "extend"
    return None


def _fence_flags(lines: list[str]) -> list[bool]:
    """Per-line flag: inside a ``` code fence (fence delimiter lines included)."""
    flags: list[bool] = []
    inside = False
    for line in lines:
        if line.lstrip().startswith("```"):
            flags.append(True)
            inside = not inside
        else:
            flags.append(inside)
    return flags


def _section_ranges(lines: list[str], fenced: list[bool]) -> dict[str, tuple[int, int]]:
    """Map normalized heading text -> (body start, body end) line index range."""
    headings: list[tuple[int, str]] = []
    for idx, line in enumerate(lines):
        if fenced[idx]:
            continue
        match = HEADING_RE.match(line.strip())
        if match:
            headings.append((idx, " ".join(match.group(2).lower().split())))
    ranges: dict[str, tuple[int, int]] = {}
    for pos, (idx, name) in enumerate(headings):
        end = headings[pos + 1][0] if pos + 1 < len(headings) else len(lines)
        ranges.setdefault(name, (idx + 1, end))
    return ranges


def _find_section(ranges: dict[str, tuple[int, int]],
                  prefix: str) -> tuple[int, int] | None:
    """First heading whose normalized text starts with prefix, else None."""
    for name, rng in ranges.items():
        if name.startswith(prefix):
            return rng
    return None


def _story_id(path: Path) -> str:
    match = STORY_ID_RE.match(path.stem)
    return match.group(1) if match else path.stem


def _parse_story(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    fenced = _fence_flags(lines)
    status = None
    for line in lines:
        match = STATUS_RE.match(line.strip())
        if match:
            status = match.group(1).strip()
            break
    markers = []
    for idx, line in enumerate(lines):
        if fenced[idx]:
            continue
        cleaned = BACKTICK_RE.sub("", line)
        if "[NEEDS CLARIFICATION" in cleaned:
            markers.append(cleaned.strip())
    return {
        "id": _story_id(path),
        "path": path,
        "open": status is None or not status.lower().startswith("done"),
        "markers": markers,
        "ranges": _section_ranges(lines, fenced),
        "lines": lines,
        "fenced": fenced,
    }


def _section_tokens(story: dict, section_prefix: str) -> list[tuple[str, str, str]]:
    """(token, before, after) for path-like backtick tokens in a section body."""
    rng = _find_section(story["ranges"], section_prefix)
    if rng is None:
        return []
    tokens: list[tuple[str, str, str]] = []
    for idx in range(rng[0], rng[1]):
        line = story["lines"][idx]
        if story["fenced"][idx]:
            continue
        for match in BACKTICK_RE.finditer(line):
            token = match.group(1).strip()
            if _is_path_token(token):
                tokens.append((token, line[:match.start()], line[match.end():]))
    return tokens


def _target_line_tokens(story: dict) -> list[str]:
    """Path-like tokens on Developer Targets target lines ("- " lines)."""
    rng = _find_section(story["ranges"], "developer targets")
    if rng is None:
        return []
    tokens: list[str] = []
    for idx in range(rng[0], rng[1]):
        line = story["lines"][idx]
        if story["fenced"][idx] or not line.strip().startswith("-"):
            continue
        for match in BACKTICK_RE.finditer(line):
            token = match.group(1).strip()
            if _is_path_token(token):
                tokens.append(token)
    return tokens


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic planning QA for story files "
                    "(ghost references, conflicts, markers, sections)")
    parser.add_argument(
        "--root", default=".",
        help="Directory containing docs/features/*/stories/*.md (default: cwd)")
    parser.add_argument(
        "--story", default=None,
        help="Check a single story file instead of the whole tree")
    args = parser.parse_args()

    root = Path(args.root)
    if not root.is_dir():
        print(f"plan_check: --root is not a directory: {root}", file=sys.stderr)
        sys.exit(2)

    story_files = sorted(root.glob("docs/features/*/stories/*.md"))
    stories = {path: _parse_story(path) for path in story_files}

    selected: set[Path] = set(stories)
    if args.story:
        story_path = Path(args.story)
        if not story_path.is_absolute():
            cwd_candidate = Path.cwd() / story_path
            story_path = (cwd_candidate if cwd_candidate.is_file()
                          else root / story_path)
        if not story_path.is_file():
            print(f"plan_check: --story file not found: {args.story}",
                  file=sys.stderr)
            sys.exit(2)
        story_path = story_path.resolve()
        if story_path not in stories:
            stories[story_path] = _parse_story(story_path)
        selected = {story_path}

    open_stories = {path: data for path, data in stories.items() if data["open"]}

    # Create-target universe: union of all open stories' Developer Targets
    # "Create"-class mentions (all section lines, verb-classified).
    create_targets: dict[str, set[str]] = {}
    for data in open_stories.values():
        for token, before, after in _section_tokens(data, "developer targets"):
            if _classify(before, after, token) == "create":
                create_targets.setdefault(token, set()).add(data["id"])

    # Touched sets for conflict detection: every path-like token on a target
    # line counts as touched, regardless of verb classification.
    touched: dict[str, set[str]] = {}
    for data in open_stories.values():
        for token in _target_line_tokens(data):
            touched.setdefault(token, set()).add(data["id"])

    conflict_candidates = [
        {"file": token, "stories": sorted(story_ids)}
        for token, story_ids in sorted(touched.items())
        if len(story_ids) > 1
    ]

    problems: list[dict] = []
    seen: set[tuple[str, str, str]] = set()
    repo_root = _repo_root()

    for path in sorted(stories):
        data = stories[path]
        if path not in selected or not data["open"]:
            continue
        sid = data["id"]

        for marker in data["markers"]:
            problems.append({
                "story": sid, "kind": "clarification-marker",
                "detail": f"unresolved [NEEDS CLARIFICATION marker: {marker}"})
        for key, label in REQUIRED_SECTIONS:
            rng = _find_section(data["ranges"], key)
            if rng is None or not any(
                    line.strip() for line in data["lines"][rng[0]:rng[1]]):
                problems.append({
                    "story": sid, "kind": "missing-section",
                    "detail": f"required section missing or empty: {label}"})

        for section_prefix in SCAN_SECTIONS:
            for token, before, after in _section_tokens(data, section_prefix):
                classification = _classify(before, after, token)
                if classification is None:
                    continue
                exists = (repo_root / token).exists()
                others = create_targets.get(token, set()) - {sid}
                if classification == "create":
                    if others and not exists:
                        detail = (f"{token} does not exist yet but is a "
                                  f"create-target of open story: "
                                  f"{', '.join(sorted(others))}")
                        key = (sid, "sequenced-reference", detail)
                        if key not in seen:
                            seen.add(key)
                            problems.append({
                                "story": sid, "kind": "sequenced-reference",
                                "detail": detail})
                    continue
                # extend/existing: the path must exist.
                if exists or token in create_targets.get(sid, set()):
                    continue
                if others:
                    detail = (f"{token} does not exist yet but is a "
                              f"create-target of open story: "
                              f"{', '.join(sorted(others))}")
                    key = (sid, "sequenced-reference", detail)
                    if key not in seen:
                        seen.add(key)
                        problems.append({
                            "story": sid, "kind": "sequenced-reference",
                            "detail": detail})
                else:
                    key = (sid, "ghost-reference", token)
                    if key not in seen:
                        seen.add(key)
                        problems.append({
                            "story": sid, "kind": "ghost-reference",
                            "detail": f"{token} referenced as existing but "
                                      f"not found in repo"})

    result = "FAIL" if any(p["kind"] in FAIL_KINDS for p in problems) else "PASS"
    print(json.dumps({
        "result": result,
        "problems": problems,
        "conflict_candidates": conflict_candidates,
    }, indent=2))
    sys.exit(1 if result == "FAIL" else 0)


if __name__ == "__main__":
    main()
