# Story 06-06 — Story management scripts (resolve, create, status-update)

Status: Planned
Traceability: REQ-013.6, REQ-013.7, REQ-013.10 → Design §13

## Definition

Three closely related scripts for story lifecycle management: resolving a story from
various input formats, creating new stories from template, and updating story status.
Bundled because they share the same file-system knowledge (feature/story layout).

## Development goal

After this story, story ID resolution, creation, and status mutation are deterministic.
Agents call these scripts instead of manually parsing FEATURES.md or editing Markdown.

## Developer Targets (exactly, no more / no less)

- Create `scripts/resolve_story.py`:
  - `resolve_story.py <input>` — accepts story ID (`06-01`), slug (`feature-hierarchy`),
    branch name (`feature/06-01-feature-hierarchy`), or partial match
  - Outputs JSON: `{"id": "06-01", "slug": "feature-hierarchy", "feature": "foundation",
    "branch": "feature/06-01-feature-hierarchy", "worktree": ".worktrees/06-01-feature-hierarchy",
    "status": "Planned", "story_file": "docs/features/foundation/stories/06-01-feature-hierarchy.md"}`
  - Exit code 0 found, 1 not found, 2 ambiguous (multiple matches)

- Create `scripts/create_story.py`:
  - `create_story.py <feature-name> <slug> --req <REQ-ID>`
  - Determines next free ID for the feature's phase
  - Copies `docs/features/_story_template.md` (real `cp`, not LLM re-generation)
  - Fills machine fields (ID, REQ-ID, status=Planned)
  - Adds entry to feature's `feature.md` story list
  - Outputs JSON: `{"story_file": "<path>", "id": "<id>"}`
  - Exit code 0 success, 1 feature not found, 2 template missing

- Create `scripts/story_status.py`:
  - `story_status.py <story-id> <new-status>` — updates status in story file header
  - Standardized labels: `Planned`, `In Progress`, `Done`, `Done (QA PASS, <hash>)`
  - Only touches the status line, no other content
  - Outputs JSON: `{"story_id": "<id>", "old_status": "...", "new_status": "..."}`
  - Exit code 0 success, 1 story not found, 2 invalid status label

- All scripts use only stdlib

## Acceptance criteria (checked by qa-manager)

- `resolve_story.py` correctly resolves story from ID, slug, branch name
- `create_story.py` creates story file from actual template copy (not LLM text)
- `create_story.py` assigns non-colliding IDs
- `story_status.py` updates only the status line, preserves all other content
- All scripts output valid JSON and use proper exit codes

## Test criteria (must exist BEFORE implementation — deterministic, no external systems)

- `tests/test_story_mgmt.py::test_resolve_by_id` — resolves story by ID
- `tests/test_story_mgmt.py::test_resolve_by_branch` — resolves story by branch name
- `tests/test_story_mgmt.py::test_resolve_not_found` — exit code 1 for unknown story
- `tests/test_story_mgmt.py::test_create_story_copies_template` — created file matches template structure
- `tests/test_story_mgmt.py::test_create_story_next_id` — ID does not collide with existing stories
- `tests/test_story_mgmt.py::test_status_update_preserves_content` — file content unchanged except status line
- `tests/test_story_mgmt.py::test_status_invalid_label` — exit code 2 for non-standard status
