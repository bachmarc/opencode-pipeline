#!/usr/bin/env python3
"""Story creation script (Stories 06-06 + 30-02).

Creates a new story from template for a given feature.

Usage:
    create_story.py <feature-name> <slug> [--feature <feature-id>]
    create_story.py <feature-name> <slug> --type debug --target-story <id>
                    [--feature <feature-id>]

Determines next free ID for the feature's phase, copies _story_template.md,
fills machine fields (ID, Feature, status=Planned), and adds entry to feature.md.

Story types (--type, Story 30-02):

- ``normal`` (default): body from _story_template.md, unchanged behavior.
  The appended ``<!-- DEBUG-STORY-BODY-TEMPLATE ... -->`` reference block in
  the template is stripped here, so normal stories remain byte-identical to
  the pre-30-02 output.
- ``debug``: INVESTIGATION story — the body skeleton is generated inline
  (Investigation questions, Deliverable: findings report <= 1 page, explicit
  rule "Do NOT fix code; do NOT change behavior"). Machine fields are
  identical to normal stories. ``--target-story`` (the story being
  investigated) is REQUIRED with --type debug and rejected otherwise.

Debug-story creation APPENDS one escalation ledger entry
``{"story": <target story id>, "debug_story": <new id>, "at": <iso8601>}``
to ``.pipeline/escalations.json`` (file created on first entry) — the
stateless driver (scripts/driver.py) counts escalations per story from this
ledger. The ledger is the ONLY escalation side effect of this script.

Outputs JSON: {"story_file": "<path>", "id": "<id>"}

Exit codes:
  0 - success
  1 - feature not found / write error / corrupt escalation ledger
  2 - template missing / argument misuse (--target-story rules violated)
"""

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

# Marker of the debug-story reference block appended to _story_template.md
# (Story 30-02). create_story.py strips everything from this marker to the
# closing "-->" when generating NORMAL stories, so normal story output stays
# byte-identical to the pre-30-02 template.
DEBUG_TEMPLATE_MARKER = "<!-- DEBUG-STORY-BODY-TEMPLATE"

# Inline body skeleton for --type debug investigation stories (Story 30-02).
# Same machine-field placeholders as _story_template.md (<ID>, <Title>,
# <feature-name> (<feature-id>)); the body is INVESTIGATION only.
DEBUG_STORY_BODY = """# Story <ID> — <Title>

Status: Planned
Feature: <feature-name> (<feature-id>)

## Codebase Snapshot

<!-- Filled by the architect when handing this investigation to a developer:
     the failing story, its QA verdict history, and the affected files/tests. -->

## Context / Purpose

<QA failure or fail loop that triggered this investigation. Goal: root-cause
clarity before more fix attempts are spent on the same loop.>

## Investigation questions

- What exactly fails? (QA verdicts, failing checkers, error output)
- Why does it fail? (root-cause hypothesis backed by file/line evidence)
- How is the failure reproduced deterministically? (commands, fixtures, test runs)
- What neighboring code is affected? (callers, dependent tests, adjacent features)

## Requirements

- Answer every investigation question with verifiable facts.
- Uncover additional bugs and gaps in the affected area; report them.
- Do NOT fix code; do NOT change behavior.

## Deliverable: findings report

A findings report of at most 1 page, facts only: symptoms, root cause,
affected files, reproduction steps, and additional bugs/gaps uncovered.

## Developer Targets (exactly, no more / no less)

- Investigate the areas listed in the Codebase Snapshot.
- Deliver the findings report (at most 1 page) in this story file.

## Acceptance criteria (checked by qa-manager)

- Findings report exists: at most 1 page, facts only.
- Every investigation question is answered with evidence.

## Test criteria (must exist BEFORE implementation)

- Not applicable — investigation story with an explicit no-fix rule; the
  deliverable is the findings report, not code.
"""


def get_next_story_id(feature_dir: Path) -> str | None:
    """Determine next free ID for the feature's phase.
    
    Reads existing story files and returns next available ID.
    Returns None if unable to determine.
    """
    stories_dir = feature_dir / "stories"
    if not stories_dir.exists():
        return None
    
    # Find all existing story IDs in this feature
    existing_ids = []
    for story_file in stories_dir.glob("*.md"):
        name = story_file.stem
        parts = name.split("-", 2)
        if len(parts) >= 2:
            try:
                phase = int(parts[0])
                story_num = int(parts[1])
                existing_ids.append((phase, story_num))
            except ValueError:
                continue
    
    if not existing_ids:
        # No existing stories, start with phase 1, ID 1
        return "01-01"
    
    # Find the phase (should be consistent within a feature)
    phases = {p for p, _ in existing_ids}
    if len(phases) != 1:
        # Multiple phases in same feature - use the first one
        phase = min(phases)
    else:
        phase = phases.pop()
    
    # Find next ID within this phase
    phase_ids = [story_num for p, story_num in existing_ids if p == phase]
    next_id = max(phase_ids) + 1 if phase_ids else 1
    
    return f"{phase:02d}-{next_id:02d}"


def add_story_to_feature_md(feature_md: Path, story_id: str, slug: str) -> bool:
    """Add story entry to feature.md Stories list.
    
    Returns True on success, False on error.
    """
    try:
        content = feature_md.read_text(encoding="utf-8")
        
        # Find the Stories section
        lines = content.splitlines(keepends=True)
        insert_idx = None
        
        for i, line in enumerate(lines):
            if line.strip() == "## Stories":
                # Find the next line after "## Stories"
                insert_idx = i + 1
                break
        
        if insert_idx is None:
            return False
        
        # Insert the new story entry
        new_entry = f"- {story_id}-{slug} (planned)\n"
        lines.insert(insert_idx + 1, new_entry)
        
        feature_md.write_text("".join(lines), encoding="utf-8")
        return True
    except (OSError, ValueError):
        return False


def strip_debug_template_block(content: str) -> str:
    """Remove the DEBUG-STORY-BODY-TEMPLATE reference block from template
    content (Story 30-02).

    The block is appended to _story_template.md at the very end; normal
    stories must stay byte-identical to the pre-30-02 output, so everything
    from the marker to the closing "-->" is cut (only when the block is the
    trailing content). Content without the marker is returned unchanged
    (backward compatible with templates of other projects).
    """
    start = content.find(DEBUG_TEMPLATE_MARKER)
    if start == -1:
        return content
    end = content.find("-->", start)
    if end == -1:
        return content  # Malformed block: leave the content untouched.
    before = content[:start].rstrip("\n")
    after = content[end + len("-->"):]
    if after.strip():
        # Unexpected content after the block — keep it (defensive).
        return before + "\n\n" + after.lstrip("\n")
    return before + "\n"


def fill_machine_fields(
    content: str, story_id: str, slug: str, feature_name: str, feature_id: str | None
) -> str:
    """Fill the machine fields shared by normal and debug stories: <ID>,
    <Title>, the Feature: line and Status: Planned."""
    content = content.replace("<ID>", story_id)
    content = content.replace("<Title>", slug.replace("-", " ").title())

    # Fill Feature: line if --feature is provided
    if feature_id:
        content = content.replace(
            "<feature-name> (<feature-id>)", f"{feature_name} ({feature_id})"
        )
    else:
        # Just fill with feature name if no feature ID provided
        content = content.replace("<feature-name> (<feature-id>)", feature_name)

    # Ensure status is "Planned"
    lines = content.splitlines(keepends=True)
    updated_lines = []
    for line in lines:
        if line.startswith("Status:"):
            updated_lines.append("Status: Planned\n")
        else:
            updated_lines.append(line)
    return "".join(updated_lines)


def append_escalation_entry(repo_root: Path, target_story: str, debug_story_id: str) -> Path:
    """Append one escalation ledger entry for a newly created debug story
    (Story 30-02).

    Appends ``{"story": target_story, "debug_story": debug_story_id,
    "at": <iso8601 UTC>}`` to ``<repo_root>/.pipeline/escalations.json``
    (file created on first entry). This ledger is the ONLY escalation side
    effect; the stateless driver counts entries per story from it.

    Returns the ledger path. Raises ValueError when the existing ledger is
    corrupt (it is never silently overwritten — escalation history must not
    be destroyed).
    """
    pipeline_dir = repo_root / ".pipeline"
    ledger = pipeline_dir / "escalations.json"
    entries: list = []
    if ledger.is_file():
        try:
            data = json.loads(ledger.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
            raise ValueError(f"Corrupt escalation ledger {ledger}: {exc}") from exc
        if isinstance(data, dict) and isinstance(data.get("escalations"), list):
            entries = data["escalations"]
        elif isinstance(data, list):
            entries = data
        else:
            raise ValueError(
                f"Escalation ledger {ledger} is not a JSON array of entries"
            )
    entries.append(
        {
            "story": target_story,
            "debug_story": debug_story_id,
            "at": datetime.now(timezone.utc).isoformat(),
        }
    )
    pipeline_dir.mkdir(parents=True, exist_ok=True)
    ledger.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    return ledger


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Create a new story from template")
    parser.add_argument("feature_name", help="Feature name (e.g., 'pipeline-evolution')")
    parser.add_argument("slug", help="Story slug (e.g., 'my-story')")
    parser.add_argument("--feature", required=False, help="Feature ID (e.g., 'F-001') to fill Feature: line")
    parser.add_argument("--req", required=False, help="(Deprecated) REQ-ID parameter, ignored")
    parser.add_argument(
        "--type",
        choices=["normal", "debug"],
        default="normal",
        help="Story type: normal (default) or debug — an INVESTIGATION story "
        "(Story 30-02) that appends an escalation ledger entry",
    )
    parser.add_argument(
        "--target-story",
        required=False,
        help="ID of the story being investigated (REQUIRED with --type debug, "
        "rejected otherwise); recorded in .pipeline/escalations.json",
    )

    args = parser.parse_args()

    # --target-story / --type combination rules (usage errors, exit 2).
    if args.type == "debug" and not args.target_story:
        print(
            json.dumps({"error": "--target-story is required with --type debug"}),
            file=sys.stderr,
        )
        return 2
    if args.type != "debug" and args.target_story:
        print(
            json.dumps({"error": "--target-story is only valid with --type debug"}),
            file=sys.stderr,
        )
        return 2

    repo_root = Path(__file__).resolve().parent.parent
    features_dir = repo_root / "docs" / "features"

    # Check if feature exists
    feature_dir = features_dir / args.feature_name
    if not feature_dir.exists():
        print(json.dumps({"error": f"Feature not found: {args.feature_name}"}), file=sys.stderr)
        return 1

    # Check if template exists (normal stories only; debug bodies are inline)
    template_file = features_dir / "_story_template.md"
    if args.type == "normal" and not template_file.exists():
        print(json.dumps({"error": "Template file not found"}), file=sys.stderr)
        return 2

    # Determine next story ID
    next_id = get_next_story_id(feature_dir)
    if not next_id:
        print(json.dumps({"error": "Unable to determine next story ID"}), file=sys.stderr)
        return 1

    # Create stories directory if needed
    stories_dir = feature_dir / "stories"
    stories_dir.mkdir(parents=True, exist_ok=True)

    # New story file
    story_filename = f"{next_id}-{args.slug}.md"
    story_file = stories_dir / story_filename

    try:
        if args.type == "debug":
            # Investigation skeleton is inline (Story 30-02); the template is
            # not used for debug stories.
            content = fill_machine_fields(
                DEBUG_STORY_BODY, next_id, args.slug, args.feature_name, args.feature
            )
            story_file.write_text(content, encoding="utf-8")
        else:
            # Copy template to new story file
            shutil.copy(str(template_file), str(story_file))

            # Fill in machine fields in the new story file
            content = story_file.read_text(encoding="utf-8")
            # Strip the appended debug-story reference block so normal stories
            # stay byte-identical to the pre-30-02 output.
            content = strip_debug_template_block(content)
            content = fill_machine_fields(
                content, next_id, args.slug, args.feature_name, args.feature
            )
            story_file.write_text(content, encoding="utf-8")
    except (OSError, ValueError) as e:
        print(json.dumps({"error": f"Failed to write story file: {e}"}), file=sys.stderr)
        return 1

    # Add entry to feature.md
    feature_md = feature_dir / "feature.md"
    if not add_story_to_feature_md(feature_md, next_id, args.slug):
        print(json.dumps({"error": "Failed to update feature.md"}), file=sys.stderr)
        return 1

    # Debug stories append the escalation ledger entry (Story 30-02) — the
    # ONLY escalation side effect of this script.
    if args.type == "debug":
        try:
            append_escalation_entry(repo_root, args.target_story, next_id)
        except (OSError, ValueError) as e:
            print(json.dumps({"error": f"Failed to append escalation ledger: {e}"}), file=sys.stderr)
            return 1

    # Output success
    result = {
        "story_file": str(story_file.relative_to(repo_root)),
        "id": next_id,
    }
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    sys.exit(main())
