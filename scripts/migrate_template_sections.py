#!/usr/bin/env python3
"""Migrate the constant sections of a project AGENTS.md to the current template.

Story 12-09: template changes (e.g. the runner-agnostic constant sections of
story 12-08) invalidate existing project AGENTS.md copies. This tool re-syncs
them deterministically:

- Replaces ONLY the constant sections (Workflow, Git conventions, Languages,
  Prohibitions) in the given project AGENTS.md with the current template
  sections (template resolved relative to THIS script's repo root — the tool
  carries the template and works from any working directory).
- Preserves everything outside those sections byte-identical (project name,
  stack, core rules, architecture, references).
- Missing constant section in the project file -> INSERT before
  "## References" (or at EOF if absent).
- Idempotent: already-current file -> {"migrated": false,
  "reason": "already current"}, exit 0, file untouched.

Exit codes:
  0 - migrated or already current
  1 - error (missing file, no recognizable constant sections)

Output: one JSON line on stdout.
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


CONSTANT_SECTIONS = [
    "## Workflow",
    "## Git conventions",
    "## Languages",
    "## Prohibitions",
]

REFERENCES_HEADING = "## References"


def extract_sections(content: str) -> Dict[str, str]:
    """Extract constant sections from markdown content.

    Same extraction logic as check_template_constancy.py: exact heading match
    up to the next "## " heading.
    """
    sections: Dict[str, str] = {}
    lines = content.split("\n")

    for section_heading in CONSTANT_SECTIONS:
        section_name = section_heading.replace("## ", "")
        start_idx = None

        for i, line in enumerate(lines):
            if line.strip() == section_heading.strip():
                start_idx = i
                break

        if start_idx is None:
            continue

        end_idx = None
        for i in range(start_idx + 1, len(lines)):
            if lines[i].startswith("## "):
                end_idx = i
                break

        if end_idx is None:
            end_idx = len(lines)

        sections[section_name] = "\n".join(lines[start_idx:end_idx])

    return sections


def normalize_lines(text: str) -> List[str]:
    """Normalize text by stripping trailing whitespace per line.

    Same comparison semantics as check_template_constancy.py.
    """
    return [line.rstrip() for line in text.split("\n")]


def resolve_template_path() -> Optional[Path]:
    """Resolve templates/AGENTS.md relative to this script's repo root."""
    script_path = Path(__file__).resolve()
    repo_root = script_path.parent.parent
    return repo_root / "templates" / "AGENTS.md"


def build_migrated_content(project_content: str, template_sections: Dict[str, str]) -> str:
    """Rebuild the project content with the constant sections re-synced.

    Non-constant content is preserved byte-identical; a blank separator line is
    inserted only where a section boundary would otherwise have none.
    """
    lines = project_content.split("\n")

    # Split into blocks at "## " boundaries: block 0 is the preamble
    # (everything before the first "## " heading), then one block per heading.
    heading_indices = [i for i, line in enumerate(lines) if line.startswith("## ")]
    bounds = [0] + heading_indices
    blocks: List[List[str]] = []
    for idx, start in enumerate(bounds):
        end = bounds[idx + 1] if idx + 1 < len(bounds) else len(lines)
        blocks.append(lines[start:end])

    out: List[str] = []
    pending_inserts = [
        heading.replace("## ", "")
        for heading in CONSTANT_SECTIONS
        if heading.replace("## ", "") not in extract_sections(project_content)
    ]

    def append_section(section_name: str) -> None:
        if out and out[-1].strip() != "":
            out.append("")  # ensure one blank line before a section heading
        section_lines = template_sections[section_name].split("\n")
        while section_lines and section_lines[-1] == "":
            section_lines.pop()  # section may already end with a blank line
        out.extend(section_lines)
        out.append("")  # exactly one trailing blank line after the section

    for idx, block in enumerate(blocks):
        if idx == 0:
            out.extend(block)  # preamble: byte-identical, no separator logic
            continue
        heading_line = block[0]
        section_name = heading_line.replace("## ", "").strip()

        # Insert missing constant sections before "## References" (or at EOF).
        if heading_line == REFERENCES_HEADING and pending_inserts:
            for insert_name in pending_inserts:
                append_section(insert_name)
            pending_inserts = []

        if heading_line in CONSTANT_SECTIONS and section_name in template_sections:
            append_section(section_name)
        else:
            if out and out[-1].strip() != "":
                out.append("")
            out.extend(block)

    for insert_name in pending_inserts:  # References absent -> insert at EOF
        append_section(insert_name)

    return "\n".join(out)


def migrate(project_path: Path, template_path: Path) -> Dict:
    """Run the migration. Returns the JSON payload; may raise SystemExit."""
    project_content = project_path.read_text(encoding="utf-8")
    template_content = template_path.read_text(encoding="utf-8")

    project_sections = extract_sections(project_content)
    template_sections = extract_sections(template_content)

    found = [s for s in project_sections if s in
             [h.replace("## ", "") for h in CONSTANT_SECTIONS]]
    if not found:
        print(json.dumps({
            "migrated": False,
            "error": "no constant sections found",
        }))
        sys.exit(1)

    # Idempotency: every constant section present and equal (modulo trailing
    # whitespace per line, same semantics as the constancy check).
    already_current = all(
        section_name in project_sections
        and normalize_lines(project_sections[section_name])
        == normalize_lines(template_sections[section_name])
        for section_name in (h.replace("## ", "") for h in CONSTANT_SECTIONS)
    )
    if already_current:
        return {"migrated": False, "reason": "already current"}

    new_content = build_migrated_content(project_content, template_sections)
    project_path.write_text(new_content, encoding="utf-8")

    migrated_names = [
        h.replace("## ", "") for h in CONSTANT_SECTIONS
    ]
    return {"migrated": True, "sections": migrated_names}


def main() -> None:
    if len(sys.argv) < 2:
        print(json.dumps({
            "migrated": False,
            "error": "Usage: migrate_template_sections.py <project-agents-md>",
        }))
        sys.exit(1)

    project_path = Path(sys.argv[1])

    if not project_path.exists():
        print(json.dumps({
            "migrated": False,
            "error": f"Project AGENTS.md not found: {project_path}",
        }))
        sys.exit(1)

    template_path = resolve_template_path()
    if template_path is None or not template_path.exists():
        print(json.dumps({
            "migrated": False,
            "error": f"Template AGENTS.md not found: {template_path}",
        }))
        sys.exit(1)

    result = migrate(project_path, template_path)
    print(json.dumps(result))
    sys.exit(0)


if __name__ == "__main__":
    main()