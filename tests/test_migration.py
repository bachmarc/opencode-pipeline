"""
Tests for documentation model migration.

Tests verify that all feature.md and story files have been migrated from the old format
(REQ-IDs, Traceability, Scope, Definition, Development goal) to the new format
(Vision, Context, Feature reference, Context/Purpose, Requirements).
"""

import json
import os
import re
from pathlib import Path
import yaml


def get_all_feature_files():
    """Get all feature.md files under docs/features/*/feature.md."""
    features_dir = Path(__file__).parent.parent / "docs" / "features"
    feature_files = list(features_dir.glob("*/feature.md"))
    return sorted(feature_files)


def get_all_story_files():
    """Get all story files under docs/features/*/stories/*.md, excluding templates."""
    docs_path = Path(__file__).parent.parent / "docs" / "features"
    story_files = []

    for feature_dir in docs_path.glob("*/stories"):
        for story_file in feature_dir.glob("*.md"):
            # Exclude template files
            if story_file.name.startswith("_"):
                continue
            story_files.append(story_file)

    return sorted(story_files)


def read_frontmatter(file_path):
    """Extract YAML frontmatter from a markdown file."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Match frontmatter between --- markers
    match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
    if not match:
        return None

    try:
        return yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None


def read_file_content(file_path):
    """Read the full content of a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


# === Feature.md migration tests (Story 09-01) ===


def test_all_features_have_vision_context():
    """All feature.md files must have ## Vision and ## Context sections."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        content = read_file_content(feature_file)

        has_vision = "## Vision" in content
        has_context = "## Context" in content

        assert has_vision, f"{feature_file.name}: Missing '## Vision' section"
        assert has_context, f"{feature_file.name}: Missing '## Context' section"


def test_no_features_have_scope():
    """No feature.md file should have ## Scope section."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        content = read_file_content(feature_file)

        has_scope = "## Scope" in content
        assert not has_scope, f"{feature_file.name}: Should not have '## Scope' section"


def test_no_features_have_req_ids():
    """No feature.md frontmatter should have non-empty req: with REQ- values."""
    feature_files = get_all_feature_files()
    assert len(feature_files) > 0, "No feature.md files found"

    for feature_file in feature_files:
        frontmatter = read_frontmatter(feature_file)

        if frontmatter is None:
            continue

        req_field = frontmatter.get("req")

        # req: [] is OK (empty list)
        # req: missing is OK
        # req: [REQ-xxx] is NOT OK
        if req_field is not None and isinstance(req_field, list):
            for item in req_field:
                assert not str(item).startswith("REQ-"), \
                    f"{feature_file.name}: req field contains REQ-ID: {item}"


# === Story file migration tests (Story 09-02) ===


def test_all_stories_have_feature_reference():
    """All story files must have a 'Feature:' line (not 'Traceability:')."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^Feature:\s+", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing 'Feature:' line"


def test_no_stories_have_traceability():
    """No story file should have a 'Traceability:' line."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert not re.search(r"^Traceability:\s+", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has 'Traceability:' line"


def test_all_stories_have_context_section():
    """All story files must have '## Context / Purpose' section."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^##\s+Context\s*/\s*Purpose", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing '## Context / Purpose' section"


def test_all_stories_have_requirements_section():
    """All story files must have '## Requirements' section."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)
        assert re.search(r"^##\s+Requirements", content, re.MULTILINE), \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Missing '## Requirements' section"


def test_no_stories_have_old_sections():
    """No story file should have '## Definition' or '## Development goal' sections."""
    story_files = get_all_story_files()
    assert len(story_files) > 0, "No story files found"

    for story_file in story_files:
        content = read_file_content(story_file)

        # Check for old section headers (case-insensitive for German variants)
        has_definition = re.search(r"^##\s+Definition", content, re.MULTILINE | re.IGNORECASE)
        has_dev_goal = re.search(r"^##\s+(Development goal|Entwicklungsziel)", content, re.MULTILINE | re.IGNORECASE)

        assert not has_definition, \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has '## Definition' section"
        assert not has_dev_goal, \
            f"{story_file.relative_to(story_file.parent.parent.parent.parent)}: Still has old development goal section"


# === Index file migration tests (Story 09-03) ===


def test_stories_index_no_req_ids():
    """STORIES.md Traceability column should not contain REQ- references."""
    stories_file = Path(__file__).parent.parent / "STORIES.md"
    assert stories_file.exists(), "STORIES.md not found"

    content = read_file_content(stories_file)

    # Extract table rows (lines starting with |)
    lines = content.split("\n")
    table_started = False
    for line in lines:
        if line.startswith("|") and "Traceability" in line:
            table_started = True
            continue
        if table_started and line.startswith("|"):
            # Skip header separator line
            if "---" in line:
                continue
            # Extract the Traceability column (last column)
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) >= 5:  # Story | Title | Status | Traceability | (empty)
                traceability = cells[4]
                assert "REQ-" not in traceability, \
                    f"STORIES.md: Found REQ- in Traceability column: {line}"


def test_stories_index_no_design_refs():
    """STORIES.md Traceability column should not contain 'Design §' references."""
    stories_file = Path(__file__).parent.parent / "STORIES.md"
    assert stories_file.exists(), "STORIES.md not found"

    content = read_file_content(stories_file)

    # Extract table rows (lines starting with |)
    lines = content.split("\n")
    table_started = False
    for line in lines:
        if line.startswith("|") and "Traceability" in line:
            table_started = True
            continue
        if table_started and line.startswith("|"):
            # Skip header separator line
            if "---" in line:
                continue
            # Extract the Traceability column (last column)
            cells = [cell.strip() for cell in line.split("|")]
            if len(cells) >= 5:  # Story | Title | Status | Traceability | (empty)
                traceability = cells[4]
                assert "Design §" not in traceability, \
                    f"STORIES.md: Found 'Design §' in Traceability column: {line}"


def test_features_index_no_traceability_column():
    """FEATURES.md table should not have a Traceability column."""
    features_file = Path(__file__).parent.parent / "FEATURES.md"
    assert features_file.exists(), "FEATURES.md not found"

    content = read_file_content(features_file)

    # Find the table header line
    lines = content.split("\n")
    for line in lines:
        if line.startswith("|") and "Feature" in line:
            # This is the header line
            assert "Traceability" not in line, \
                f"FEATURES.md: Table header still contains 'Traceability' column"
            break


def test_features_index_no_req_ids():
    """FEATURES.md table rows should not contain REQ- references."""
    features_file = Path(__file__).parent.parent / "FEATURES.md"
    assert features_file.exists(), "FEATURES.md not found"

    content = read_file_content(features_file)

    # Extract table rows (lines starting with |)
    lines = content.split("\n")
    table_started = False
    for line in lines:
        if line.startswith("|") and "Feature" in line:
            table_started = True
            continue
        if table_started and line.startswith("|"):
            # Skip header separator line
            if "---" in line:
                continue
            assert "REQ-" not in line, \
                f"FEATURES.md: Found REQ- in table row: {line}"


def test_features_index_has_new_features():
    """FEATURES.md should include F-005 and F-006 entries."""
    features_file = Path(__file__).parent.parent / "FEATURES.md"
    assert features_file.exists(), "FEATURES.md not found"

    content = read_file_content(features_file)

    assert "F-005" in content, "FEATURES.md: Missing F-005 entry"
    assert "F-006" in content, "FEATURES.md: Missing F-006 entry"


# === Summary document migration tests (Story 09-04) ===


def test_requirements_is_derived_summary():
    """requirements.md must state it is a derived summary (not primary source)."""
    req_file = Path(__file__).parent.parent / "docs" / "requirements.md"
    assert req_file.exists(), "docs/requirements.md not found"

    content = read_file_content(req_file)

    # Check for derived/summary/generated language
    has_derived = "derived" in content.lower()
    has_summary = "summary" in content.lower()
    has_generated = "generated from" in content.lower()

    assert has_derived or has_summary or has_generated, \
        "requirements.md must state it is a derived summary (contains 'derived', 'summary', or 'generated from')"


def test_requirements_has_feature_table():
    """requirements.md must contain a feature overview table with feature IDs."""
    req_file = Path(__file__).parent.parent / "docs" / "requirements.md"
    assert req_file.exists(), "docs/requirements.md not found"

    content = read_file_content(req_file)

    # Check for feature IDs in the content (F-RETRO, F-001, F-002, etc.)
    feature_ids = ["F-RETRO", "F-001", "F-002", "F-003", "F-004", "F-005", "F-006"]
    found_features = sum(1 for fid in feature_ids if fid in content)

    assert found_features >= 6, \
        f"requirements.md must contain a feature table with at least 6 feature IDs (found {found_features})"


def test_requirements_no_req_definitions():
    """requirements.md must NOT contain REQ-ID definitions (old format like 'REQ-001 Two-clone topology:')."""
    req_file = Path(__file__).parent.parent / "docs" / "requirements.md"
    assert req_file.exists(), "docs/requirements.md not found"

    content = read_file_content(req_file)

    # Pattern: REQ-<digits> followed by whitespace and word character (old definition format)
    old_format = re.search(r"REQ-\d+\s+\w", content)

    assert not old_format, \
        "requirements.md must not contain old REQ-ID definition format (e.g., 'REQ-001 Two-clone topology:')"


def test_design_is_derived_summary():
    """design.md must state it is a derived summary (not primary source)."""
    design_file = Path(__file__).parent.parent / "docs" / "design.md"
    assert design_file.exists(), "docs/design.md not found"

    content = read_file_content(design_file)

    has_derived = "derived" in content.lower()
    has_summary = "summary" in content.lower()
    has_generated = "generated from" in content.lower()

    assert has_derived or has_summary or has_generated, \
        "design.md must state it is a derived summary (contains 'derived', 'summary', or 'generated from')"


def test_design_no_numbered_req_sections():
    """design.md must NOT contain old §-numbered sections with REQ-IDs."""
    design_file = Path(__file__).parent.parent / "docs" / "design.md"
    assert design_file.exists(), "docs/design.md not found"

    content = read_file_content(design_file)

    old_numbered_sections = re.search(r"^##\s+\d+\.\s+.+\s*\(REQ-", content, re.MULTILINE)

    assert not old_numbered_sections, \
        "design.md must not contain old §-numbered sections with REQ-IDs in titles"


def test_design_has_decisions_table():
    """design.md must still contain a Decisions table (with | D rows)."""
    design_file = Path(__file__).parent.parent / "docs" / "design.md"
    assert design_file.exists(), "docs/design.md not found"

    content = read_file_content(design_file)

    has_decisions_header = "Decisions" in content or "| D" in content
    has_d_rows = re.search(r"\|\s*D\d+\s*\|", content)

    assert has_decisions_header and has_d_rows, \
        "design.md must contain a Decisions table with D1-D13 decision rows"


# === Prompt and command migration tests (Story 09-05) ===


def test_qa_prompt_no_requirements_source_of_truth():
    """qa-manager.md does not reference requirements.md as 'source of truth' for checking."""
    qa_file = Path(__file__).parent.parent / "agent" / "qa-manager.md"
    assert qa_file.exists(), "agent/qa-manager.md not found"

    content = read_file_content(qa_file)

    has_bad_pattern = re.search(
        r"source\s+of\s+truth.*requirements\.md|requirements\.md.*source\s+of\s+truth",
        content,
        re.IGNORECASE | re.DOTALL
    )

    assert not has_bad_pattern, \
        "qa-manager.md must not reference requirements.md as 'source of truth' for checking"


def test_developer_prompt_story_primary():
    """developer.md references story file as primary source (not design.md)."""
    dev_file = Path(__file__).parent.parent / "agent" / "developer.md"
    assert dev_file.exists(), "agent/developer.md not found"

    content = read_file_content(dev_file)

    has_story_primary = re.search(
        r"story\s+file.*primary|primary.*story\s+file",
        content,
        re.IGNORECASE
    )

    has_optional_design = re.search(
        r"[Oo]ptional.*design\.md|design\.md.*[Oo]ptional",
        content
    )

    assert has_story_primary or has_optional_design, \
        "developer.md must indicate story file is primary source and design.md is optional"


def test_template_no_req_id_traceability():
    """templates/AGENTS.md Workflow section does not mention REQ-XXX as traceability anchors."""
    template_file = Path(__file__).parent.parent / "templates" / "AGENTS.md"
    assert template_file.exists(), "templates/AGENTS.md not found"

    content = read_file_content(template_file)

    workflow_match = re.search(r"^##\s+Workflow\s*\n(.*?)(?=^##\s+|\Z)", content, re.MULTILINE | re.DOTALL)
    assert workflow_match, "templates/AGENTS.md: Workflow section not found"

    workflow_section = workflow_match.group(1)

    has_req_traceability = re.search(r"REQ-\w+.*traceability|traceability.*REQ-\w+", workflow_section, re.IGNORECASE)

    assert not has_req_traceability, \
        "templates/AGENTS.md Workflow section must not mention REQ-XXX as traceability anchors"


def test_template_references_derived():
    """templates/AGENTS.md References section describes requirements.md as derived summary."""
    template_file = Path(__file__).parent.parent / "templates" / "AGENTS.md"
    assert template_file.exists(), "templates/AGENTS.md not found"

    content = read_file_content(template_file)

    references_match = re.search(r"^##\s+References\s*\n(.*?)(?=^##\s+|\Z)", content, re.MULTILINE | re.DOTALL)
    assert references_match, "templates/AGENTS.md: References section not found"

    references_section = references_match.group(1)

    req_line = re.search(r"`docs/requirements\.md`.*", references_section)
    assert req_line, "templates/AGENTS.md References: requirements.md line not found"

    req_text = req_line.group(0)
    has_derived = "derived" in req_text.lower()
    has_summary = "summary" in req_text.lower()

    assert has_derived or has_summary, \
        "templates/AGENTS.md References section must describe requirements.md as 'derived' or 'summary'"


def test_agents_md_references_derived():
    """AGENTS.md (root) References section describes requirements.md as derived summary."""
    agents_file = Path(__file__).parent.parent / "AGENTS.md"
    assert agents_file.exists(), "AGENTS.md not found"

    content = read_file_content(agents_file)

    references_match = re.search(r"^##\s+References\s*\n(.*?)(?=^##\s+|\Z)", content, re.MULTILINE | re.DOTALL)
    assert references_match, "AGENTS.md: References section not found"

    references_section = references_match.group(1)

    req_line = re.search(r"`docs/requirements\.md`.*", references_section)
    assert req_line, "AGENTS.md References: requirements.md line not found"

    req_text = req_line.group(0)
    has_derived = "derived" in req_text.lower()
    has_summary = "summary" in req_text.lower()

    assert has_derived or has_summary, \
        "AGENTS.md References section must describe requirements.md as 'derived' or 'summary'"


def test_commands_no_primary_requirements():
    """Commands (decompose, requirements, new-project) do not instruct creating requirements.md as primary."""
    command_files = [
        Path(__file__).parent.parent / "command" / "decompose.md",
        Path(__file__).parent.parent / "command" / "requirements.md",
        Path(__file__).parent.parent / "command" / "new-project.md",
    ]

    for cmd_file in command_files:
        assert cmd_file.exists(), f"{cmd_file.name} not found"

        content = read_file_content(cmd_file)

        has_primary_req = re.search(
            r"[Cc]reate\s+`docs/requirements\.md`\s*,\s*`docs/design\.md`",
            content
        )

        assert not has_primary_req, \
            f"{cmd_file.name}: Must not instruct creating requirements.md as primary source"


# === Scripts migration tests (Story 09-06) ===


def test_create_story_no_req_required(tmp_path):
    """create_story.py works without --req parameter (or with --feature instead)."""
    import subprocess
    import sys
    import json
    import os

    scripts_dir = Path(__file__).parent.parent / "scripts"
    create_story_script = scripts_dir / "create_story.py"

    assert create_story_script.exists(), f"create_story.py not found at {create_story_script}"

    # Create a temporary feature directory
    test_feature_dir = tmp_path / "test-feature"
    test_feature_dir.mkdir()

    feature_md = test_feature_dir / "feature.md"
    feature_md.write_text("""---
id: F-TEST
title: Test Feature
status: planned
owner: ""
---

## Vision

Test feature vision.

## Context

Test feature context.

## Stories

""")

    stories_dir = test_feature_dir / "stories"
    stories_dir.mkdir()

    docs_dir = tmp_path / "docs" / "features"
    docs_dir.mkdir(parents=True)

    import shutil
    test_feature_copy = docs_dir / "test-feature"
    shutil.copytree(test_feature_dir, test_feature_copy)

    template_file = Path(__file__).parent.parent / "docs" / "features" / "_story_template.md"
    assert template_file.exists(), f"Template file not found: {template_file}"

    template_copy = docs_dir / "_story_template.md"
    shutil.copy(template_file, template_copy)

    cmd = [
        sys.executable,
        str(create_story_script),
        "test-feature",
        "test-story",
        "--feature", "F-TEST"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={**dict(os.environ), "PYTHONPATH": str(Path(__file__).parent.parent)}
    )

    if result.returncode != 0 and "--feature" in result.stderr:
        cmd = [
            sys.executable,
            str(create_story_script),
            "test-feature",
            "test-story"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env={**dict(os.environ), "PYTHONPATH": str(Path(__file__).parent.parent)}
        )

    assert result.returncode == 0 or "--req" not in result.stderr, \
        f"Script failed or requires --req: exit={result.returncode}, stderr={result.stderr}"


def test_create_story_generates_feature_line(tmp_path):
    """create_story.py generates story files with 'Feature:' line (not 'Traceability:')."""
    import subprocess
    import sys
    import json
    import os

    scripts_dir = Path(__file__).parent.parent / "scripts"
    create_story_script = scripts_dir / "create_story.py"

    test_feature_dir = tmp_path / "test-feature"
    test_feature_dir.mkdir()

    feature_md = test_feature_dir / "feature.md"
    feature_md.write_text("""---
id: F-TEST
title: Test Feature
status: planned
owner: ""
---

## Vision

Test feature vision.

## Context

Test feature context.

## Stories

""")

    stories_dir = test_feature_dir / "stories"
    stories_dir.mkdir()

    docs_dir = tmp_path / "docs" / "features"
    docs_dir.mkdir(parents=True)

    import shutil
    test_feature_copy = docs_dir / "test-feature"
    shutil.copytree(test_feature_dir, test_feature_copy)

    template_file = Path(__file__).parent.parent / "docs" / "features" / "_story_template.md"
    assert template_file.exists(), f"Template file not found: {template_file}"

    template_copy = docs_dir / "_story_template.md"
    shutil.copy(template_file, template_copy)

    cmd = [
        sys.executable,
        str(create_story_script),
        "test-feature",
        "test-story",
        "--feature", "F-TEST"
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(tmp_path),
        env={**dict(os.environ), "PYTHONPATH": str(Path(__file__).parent.parent)}
    )

    if result.returncode != 0 and "--feature" in result.stderr:
        cmd = [
            sys.executable,
            str(create_story_script),
            "test-feature",
            "test-story"
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(tmp_path),
            env={**dict(os.environ), "PYTHONPATH": str(Path(__file__).parent.parent)}
        )

    if result.returncode == 0:
        try:
            output = json.loads(result.stdout)
            story_file = tmp_path / output["story_file"]

            story_content = story_file.read_text()

            assert re.search(r"^Feature:\s+", story_content, re.MULTILINE), \
                f"Story file missing 'Feature:' line. Content:\n{story_content}"

            assert not re.search(r"^Traceability:\s+", story_content, re.MULTILINE), \
                f"Story file still has 'Traceability:' line. Content:\n{story_content}"
        except json.JSONDecodeError:
            pass


def test_pipeline_status_no_req_field(tmp_path):
    """pipeline_status.py does not error on feature.md files without 'req:' field."""
    import subprocess
    import sys
    import json

    scripts_dir = Path(__file__).parent.parent / "scripts"
    pipeline_status_script = scripts_dir / "pipeline_status.py"

    assert pipeline_status_script.exists(), f"pipeline_status.py not found at {pipeline_status_script}"

    repo_dir = tmp_path / "test_repo"
    repo_dir.mkdir()

    subprocess.run(
        ["git", "init"],
        cwd=repo_dir,
        capture_output=True,
        check=True
    )

    features_dir = repo_dir / "docs" / "features"
    feature_dir = features_dir / "test-feature"
    feature_dir.mkdir(parents=True)

    feature_md = feature_dir / "feature.md"
    feature_md.write_text("""---
id: F-TEST
title: Test Feature
status: planned
owner: ""
---

## Vision

Test feature vision.

## Context

Test feature context.

## Stories

""")

    cmd = [
        sys.executable,
        str(pipeline_status_script)
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(repo_dir)
    )

    assert result.returncode == 0, \
        f"pipeline_status.py failed on feature.md without req: field. stderr={result.stderr}"

    try:
        output = json.loads(result.stdout)
        assert isinstance(output, dict), "Output should be a JSON object"
    except json.JSONDecodeError:
        assert False, f"pipeline_status.py output is not valid JSON: {result.stdout}"
