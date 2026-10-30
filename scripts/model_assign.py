#!/usr/bin/env python3
"""Deterministic tier-to-model appliance (Story 31-01).

Reads a local role map (JSON: ``{role: {tier, provider_model}}``) and patches
the local opencode config's ``agent.<role>.model`` lines accordingly. The
official OpenCode v2 config key is ``agent`` (singular); the legacy ``agents``
(plural) key is patched only as a deterministic fallback, and a config with
BOTH keys is refused as ambiguous. The architect never discusses model
assignments in conversation; running this script IS the assignment.

Subcommands (mutually exclusive flags):
    --show    print the current role map as JSON
    --init    write a minimal default map (roles: architect, developer,
              qa-manager; tier "cheap"; empty provider_model). Refuses to
              overwrite an existing map.
    --apply   patch the config: for every role present in BOTH the map and
              the config's ``agent`` object (legacy ``agents`` as fallback),
              set ``model`` to the map's ``provider_model``. Roles in the
              map but not in the config are reported as ``skipped``.

Conventions:
    - Paths: ``--map`` (default ``~/.pipeline/model_map.json``),
      ``--config`` (default ``~/.config/opencode/opencode.jsonc``).
    - JSONC safety: the config may contain comments. Only the
      ``agent.<role>.model`` value lines are patched — comments and all
      other lines stay byte-identical. On any ambiguity (both ``agent`` and
      ``agents`` keys, duplicate role block, duplicate ``model`` key inside
      a role block, non-string/unsafe model value) the script exits 1
      WITHOUT writing.
    - Model strings are opaque: they are copied verbatim, never validated
      or padded.
    - No concrete model or provider names appear in this script (role
      abstraction).
    - pathlib only (Windows/Linux path safety).

Exit code: 0 on success, 1 on error. On success --show/--apply print a JSON
result to stdout; errors go to stderr.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

DEFAULT_MAP_PATH = Path.home() / ".pipeline" / "model_map.json"
DEFAULT_CONFIG_PATH = Path.home() / ".config" / "opencode" / "opencode.jsonc"

DEFAULT_ROLES = ("architect", "developer", "qa-manager")
DEFAULT_TIER = "cheap"

# Structure patterns (matched against comment-stripped lines).
# Primary config key is "agent" (singular, OpenCode v2 docs); the legacy
# plural "agents" is patched only as a deterministic fallback. Both keys
# present = ambiguous = refuse.
RE_AGENT_KEY = re.compile(r'^\s*"agent"\s*:\s*\{')
RE_AGENTS_KEY = re.compile(r'^\s*"agents"\s*:\s*\{')
RE_ROLE_KEY = re.compile(r'^\s*"([^"]+)"\s*:\s*\{')
RE_MODEL_KEY = re.compile(r'^\s*"model"\s*:')

# A patchable model line: single-line, plain string value (no escapes),
# optional trailing comma/comment. Group 2 is the value to replace.
RE_MODEL_LINE = re.compile(r'^(\s*"model"\s*:\s*)"([^"\\]*)"(.*)$')


class PatchError(Exception):
    """Raised when the config cannot be patched unambiguously."""


# --- JSONC-aware line scanning --------------------------------------------------


def _strip_comments(lines: list[str]) -> tuple[list[str], list[str]]:
    """Remove JSONC comments from lines while preserving structure.

    Returns two parallel lists over the same lines:
      - ``code``: the line with comments removed (string literals kept).
      - ``blank``: the line with comments removed AND string literals
        blanked to spaces — only structural characters ({}[]:,) remain,
        so brace-depth tracking cannot be fooled by braces inside strings.

    Raises PatchError on an unterminated string literal (strings may not
    span lines in JSON).
    """
    code: list[str] = []
    blank: list[str] = []
    in_string = False
    in_block = False
    escaped = False
    for line in lines:
        buf_code: list[str] = []
        buf_blank: list[str] = []
        i = 0
        n = len(line)
        while i < n:
            ch = line[i]
            if in_block:
                if ch == "*" and i + 1 < n and line[i + 1] == "/":
                    in_block = False
                    i += 2
                    continue
                buf_blank.append(" ")
                i += 1
                continue
            if in_string:
                if escaped:
                    escaped = False
                elif ch == "\\":
                    escaped = True
                elif ch == '"':
                    in_string = False
                buf_code.append(ch)
                buf_blank.append(" ")
                i += 1
                continue
            if ch == '"':
                in_string = True
                buf_code.append(ch)
                buf_blank.append(" ")
                i += 1
                continue
            if ch == "/" and i + 1 < n and line[i + 1] == "/":
                break  # line comment: rest of line is comment
            if ch == "/" and i + 1 < n and line[i + 1] == "*":
                in_block = True
                buf_blank.append("  ")
                i += 2
                continue
            buf_code.append(ch)
            buf_blank.append(ch)
            i += 1
        if in_string and not in_block:
            # A JSON string cannot span lines.
            raise PatchError("unterminated string literal in config")
        code.append("".join(buf_code))
        blank.append("".join(buf_blank))
    if in_block:
        raise PatchError("unterminated block comment in config")
    return code, blank


def _depth_scan(blank: list[str], start: int, opening_depth: int) -> int:
    """Return the line index whose closing brace balances the opener at ``start``.

    ``opening_depth`` is the brace depth BEFORE the opener's ``{`` on line
    ``start``; the block ends when depth returns to that value.
    """
    depth = opening_depth
    for i in range(start, len(blank)):
        for ch in blank[i]:
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
                if depth == opening_depth:
                    return i
    raise PatchError("unbalanced braces in config (cannot find block end)")


# --- map handling ----------------------------------------------------------------


def load_map(map_path: Path) -> dict:
    """Load and structurally validate the role map.

    Structure (not model values): ``{role: {tier: ..., provider_model: str}}``.
    """
    if not map_path.is_file():
        raise SystemExit(
            f"error: role map not found: {map_path}\n"
            f"hint: run with --init to create a minimal map"
        )
    try:
        data = json.loads(map_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"error: cannot parse role map {map_path}: {exc}") from None
    if not isinstance(data, dict):
        raise SystemExit(f"error: role map must be a JSON object: {map_path}")
    for role, entry in data.items():
        if not isinstance(entry, dict) or not isinstance(
            entry.get("provider_model"), str
        ):
            raise SystemExit(
                f"error: role map entry for {role!r} must be an object with a "
                f"string 'provider_model' field"
            )
    return data


def cmd_show(map_path: Path) -> int:
    """Print the current role map as JSON."""
    data = load_map(map_path)
    print(json.dumps(data, indent=2))
    return 0


def cmd_init(map_path: Path) -> int:
    """Write a minimal default map; refuse to overwrite an existing one."""
    if map_path.exists():
        print(
            f"error: role map already exists: {map_path} (not overwritten)",
            file=sys.stderr,
        )
        return 1
    default_map = {
        role: {"tier": DEFAULT_TIER, "provider_model": ""} for role in DEFAULT_ROLES
    }
    try:
        map_path.parent.mkdir(parents=True, exist_ok=True)
        map_path.write_text(
            json.dumps(default_map, indent=2) + "\n", encoding="utf-8"
        )
    except OSError as exc:
        print(f"error: cannot write role map {map_path}: {exc}", file=sys.stderr)
        return 1
    print(f"wrote minimal role map: {map_path}")
    return 0


# --- config patching --------------------------------------------------------------


def _locate_agent_object(
    code: list[str], blank: list[str]
) -> tuple[int, int, int, str] | None:
    """Find the agent object: ``agent`` (primary) or legacy ``agents``.

    Deterministic key policy (no heuristics): exactly one ``agent`` object ->
    patch it; no ``agent`` but exactly one legacy ``agents`` object -> patch
    that; both keys present -> ambiguity, refuse. Neither key -> ``None``
    (every role is then reported as skipped, nothing to patch).

    Returns (open_line, close_line, depth_before_open, key) or ``None``.
    Raises PatchError on the both-keys ambiguity.
    """
    primary = [i for i, line in enumerate(code) if RE_AGENT_KEY.match(line)]
    legacy = [i for i, line in enumerate(code) if RE_AGENTS_KEY.match(line)]
    if primary and legacy:
        raise PatchError(
            "ambiguous config: both 'agent' and 'agents' objects present; "
            "refusing to patch"
        )
    if not primary and not legacy:
        return None
    matches = primary if primary else legacy
    key = "agent" if primary else "agents"
    if len(matches) != 1:
        raise PatchError(
            f"expected exactly one '\"{key}\"' object in config, "
            f"found {len(matches)}"
        )
    start = matches[0]
    # brace depth accumulated by all lines before the agent key line
    depth = 0
    for i in range(start):
        for ch in blank[i]:
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
    end = _depth_scan(blank, start, depth)
    return start, end, depth, key


def _collect_patches(
    lines: list[str],
    code: list[str],
    blank: list[str],
    agent_start: int,
    agent_end: int,
    agent_depth: int,
    config_key: str,
    role_model: dict[str, str],
) -> tuple[dict[int, str], dict[str, dict[str, str]], list[str]]:
    """Compute the new model lines for each role present in the config.

    Returns (patches: {line_index: new_line}, applied, skipped_roles) where
    each applied entry is ``{"model": <new value>, "key": config_key}``
    recording which top-level object was patched. Raises PatchError on any
    ambiguity. Nothing is written here.
    """
    patches: dict[int, str] = {}
    applied: dict[str, dict[str, str]] = {}
    skipped: list[str] = []

    # find role blocks at the direct child level of the agent object
    role_openers: dict[str, int] = {}
    depth = agent_depth
    for i in range(agent_start, agent_end + 1):
        pre_depth = depth
        for ch in blank[i]:
            if ch in "{[":
                depth += 1
            elif ch in "}]":
                depth -= 1
        if i == agent_start:
            continue  # the agent key line itself
        if pre_depth == agent_depth + 1:
            match = RE_ROLE_KEY.match(code[i])
            if match and blank[i].rstrip().endswith("{"):
                role = match.group(1)
                if role in role_openers:
                    raise PatchError(f"duplicate agent role block: {role!r}")
                role_openers[role] = i

    for role in role_model:
        new_model = role_model[role]
        if role not in role_openers:
            skipped.append(role)
            continue
        block_start = role_openers[role]
        block_end = _depth_scan(blank, block_start, agent_depth + 1)

        # find the model lines inside this role block (direct key level)
        model_lines: list[int] = []
        depth = agent_depth + 1
        for i in range(block_start, block_end + 1):
            pre_depth = depth
            for ch in blank[i]:
                if ch in "{[":
                    depth += 1
                elif ch in "}]":
                    depth -= 1
            if pre_depth == agent_depth + 2 and RE_MODEL_KEY.match(code[i]):
                model_lines.append(i)

        if len(model_lines) != 1:
            raise PatchError(
                f"role {role!r}: expected exactly one '\"model\"' key in its "
                f"block, found {len(model_lines)}"
            )
        line_idx = model_lines[0]
        # strip the line ending so it survives the patch byte-identically
        raw_line = lines[line_idx]
        eol = raw_line[len(raw_line.rstrip("\r\n")):]
        match = RE_MODEL_LINE.match(raw_line.rstrip("\r\n"))
        if not match:
            raise PatchError(
                f"role {role!r}: '\"model\"' value is not a plain single-line "
                f"string; refusing to patch"
            )
        value = match.group(2)
        if value == new_model:
            continue  # already correct — nothing to change
        if '"' in new_model or "\\" in new_model or "\n" in new_model:
            raise PatchError(
                f"role {role!r}: new model value contains unsafe characters; "
                f"refusing to write"
            )
        patches[line_idx] = match.group(1) + '"' + new_model + '"' + match.group(3) + eol
        applied[role] = {"model": new_model, "key": config_key}

    return patches, applied, skipped


def cmd_apply(map_path: Path, config_path: Path) -> int:
    """Patch the config's agent.<role>.model lines from the role map.

    Key policy: patch the primary ``agent`` object; fall back to the legacy
    ``agents`` object only when ``agent`` is absent; refuse (exit 1, no
    write) when both are present. No agent object at all -> every role is
    reported as skipped.
    """
    data = load_map(map_path)
    role_model = {role: entry["provider_model"] for role, entry in data.items()}

    if not config_path.is_file():
        print(f"error: config not found: {config_path}", file=sys.stderr)
        return 1
    try:
        text = config_path.read_text(encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot read config {config_path}: {exc}", file=sys.stderr)
        return 1

    lines = text.splitlines(keepends=True)
    try:
        code, blank = _strip_comments(lines)
        located = _locate_agent_object(code, blank)
        if located is None:
            patches, applied, skipped = {}, {}, sorted(role_model)
        else:
            agent_start, agent_end, agent_depth, config_key = located
            patches, applied, skipped = _collect_patches(
                lines,
                code,
                blank,
                agent_start,
                agent_end,
                agent_depth,
                config_key,
                role_model,
            )
    except PatchError as exc:
        print(f"error: cannot patch config unambiguously: {exc}", file=sys.stderr)
        return 1

    if patches:
        for line_idx, new_line in patches.items():
            lines[line_idx] = new_line
        try:
            config_path.write_text("".join(lines), encoding="utf-8")
        except OSError as exc:
            print(f"error: cannot write config {config_path}: {exc}", file=sys.stderr)
            return 1

    print(
        json.dumps(
            {
                "result": "PASS",
                "applied": applied,
                "skipped": skipped,
            },
            indent=2,
        )
    )
    return 0


# --- CLI --------------------------------------------------------------------------


def main() -> int:
    """Parse flags and dispatch to the requested subcommand."""
    parser = argparse.ArgumentParser(
        description=(
            "Deterministic tier-to-model appliance: patches the local opencode "
            "config's agent.<role>.model values from a role map file (legacy "
            "'agents' plural key patched only as fallback; both keys = refuse)."
        )
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument(
        "--show",
        action="store_true",
        help="print the current role map as JSON",
    )
    mode.add_argument(
        "--init",
        action="store_true",
        help="write a minimal default role map (refuses to overwrite)",
    )
    mode.add_argument(
        "--apply",
        action="store_true",
        help="patch agent.<role>.model in the local opencode config",
    )
    parser.add_argument(
        "--map",
        type=Path,
        default=DEFAULT_MAP_PATH,
        help="path to the role map JSON (default: ~/.pipeline/model_map.json)",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=DEFAULT_CONFIG_PATH,
        help="path to the opencode config (default: ~/.config/opencode/opencode.jsonc)",
    )
    args = parser.parse_args()

    if args.show:
        return cmd_show(args.map)
    if args.init:
        return cmd_init(args.map)
    return cmd_apply(args.map, args.config)


if __name__ == "__main__":
    sys.exit(main())
