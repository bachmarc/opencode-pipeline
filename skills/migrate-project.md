---
description: Guide Architect through 6-phase project migration workflow
mode: skill
---

# migrate-project Skill — 6-Phase Migration Workflow

This skill guides the Architect through migrating an existing project into the opencode pipeline framework. The migration is deterministic and non-destructive — it analyzes the project, generates configuration files, and provisions missing structure without modifying source code.

## Phase 1: Analyze Project Structure

Run the project analyzer to understand the current state:

```bash
python analyze_project.py <path>
```

This script:
- Scans the project directory for existing structure (git, source code, tests, docs)
- Detects the main branch name (main, master, develop, etc.)
- Identifies the tech stack (Python, TypeScript, Go, etc.)
- Detects test command and deployment hints
- Returns JSON analysis with project metadata

**Output:** JSON object with keys like `project_name`, `main_branch`, `tech_stack`, `has_git`, `has_src`, `has_tests`, `test_command`, `deploy_hints`, `existing_agents_md`, etc.

## Phase 2: Present Analysis & Confirm Stack, Test Command, and Deploy Method

Present the analysis results to the user:

1. **Show the detected project metadata:**
    - Project name
    - Current main branch name
    - Detected tech stack
    - Existing structure (git, source, tests, docs)

2. **Confirm with user:**
    - Is the detected main branch name correct? (If not, ask for the correct name)
    - Is the tech stack correct? (If not, ask for corrections)
    - Are there any special considerations for this project?

3. **Confirm test command:**
    - Present the detected `test_command` from the analysis
    - Ask: "Is this the correct test command for your project?"
    - Options:
      - "Yes, confirmed" → Use detected command, derive `qa_checker` from it
      - "No, correct it" → Ask for the correct command, derive `qa_checker` from corrected command
      - "I'll configure manually later" → Set `qa_checker="unknown"`, skip qa_config.json generation
    - Store the confirmed test command and derived `qa_checker` for Phase 4

4. **Confirm deployment method:**
    - Present the detected `deploy_hints` from the analysis
    - Ask: "How is this project deployed?"
    - Provide options: `git-push`, `scp`, `docker`, `ci-cd`, `mcp`, `manual`, `other` (with free text input)
    - Allow multiple selections
    - Store confirmed deploy methods for Phase 4

5. **Extract existing AGENTS.md content (if present):**
    - If the project already has an AGENTS.md file, read it
    - Extract project-specific sections (stack, core rules, architecture notes)
    - These will be used in Phase 3 to preserve existing context

## Phase 3: Interactive AGENTS.md Generation

Generate the AGENTS.md file for the project:

1. **Use the prepare AGENTS.md workflow to create a draft:**
     ```bash
     python prepare_agents_md.py <path> --existing-agents <path-to-existing-agents-if-any>
     ```
     This script:
    - Loads the template from `~/.config/opencode/templates/AGENTS.md`
    - Fills in project-specific sections based on the analysis
    - Preserves existing project context if AGENTS.md already exists
    - Returns a draft AGENTS.md file

2. **Review the draft with the user:**
    - Show the generated AGENTS.md
    - Ask for corrections or additions to project-specific sections:
      - Project description (What is this project?)
      - Stack (languages, frameworks, tools)
      - Core rules (any special constraints or patterns?)
      - Architecture notes (function vs connectivity)
      - Git conventions (branch naming, commit style)
      - Workflow (any deviations from the standard?)

3. **Finalize AGENTS.md:**
    - Incorporate user feedback
    - Write the final AGENTS.md to the project root

**IMPORTANT:** Do NOT modify source code (`src/`, `tests/`, `main.py`, etc.) during this phase. Only generate configuration files.

## Phase 4: Provision Missing Structure

Create the missing directory structure and template files:

```bash
python provision_structure.py <path> <analysis_json> --qa-checker "<qa_checker>" --deploy-methods "<method1>" "<method2>" ...
```

Or call it programmatically with the confirmed values from Phase 2:

```python
from scripts.provision_structure import provision_structure
provision_structure(
    target_path=<path>,
    analysis=<analysis_dict>,
    qa_checker="<qa_checker>",  # From Phase 2 test command confirmation
    deploy_methods=["<method1>", "<method2>", ...]  # From Phase 2 deploy method confirmation
)
```

This script:
- Creates missing directories: `docs/features/`, `STORIES.md`, `tests/fakes/`, `.pipeline/`, etc.
- Creates template files: `docs/features/_feature_template.md`, `docs/features/_story_template.md`
- Creates `.gitignore` if missing
- Writes `qa_config.json` if `qa_checker` is provided and not "unknown"
- Appends `## Deployment` section to `AGENTS.md` if `deploy_methods` is provided
- Does NOT overwrite existing files

**Output:** Report with list of created/skipped directories and files.

## Phase 5: Optional Retro Stories (User Choice)

Ask the user if they want to create "retro stories" for existing work:

1. **Ask the user:**
    - "Would you like to create retro stories for existing work? (yes/no)"
    - If yes: "How granular? (fine-grained: one story per feature, coarse: one story per major phase)"

2. **If user chooses yes, run the create retro stories workflow:**
     ```bash
     python create_retro_stories.py <path> --granularity <fine|coarse>
     ```
     This script:
    - Analyzes git history (if available)
    - Generates story files for past work
    - Creates a STORIES.md index
    - Marks stories as "Done" (historical)

3. **If user chooses no:**
    - Skip this phase
    - Continue to Phase 6

## Phase 6: Validate Migration

Verify that the migration was successful:

```bash
python validate_migration.py <path>
```

This script:
- Checks that all required files exist (AGENTS.md, STORIES.md, docs/features/, tests/fakes/, etc.)
- Validates AGENTS.md frontmatter and structure
- Checks that git is initialized
- Verifies that source code was not modified
- Validates that AGENTS.md contains a `## Deployment` section with real content
- Returns a validation report

**Output:** Validation report with status (PASS/FAIL) and any issues found.

## Summary

After all 6 phases:
- The project has a complete opencode pipeline structure
- AGENTS.md is configured for the project
- All required directories and templates exist
- `qa_config.json` is configured with the project's test command (if not manually deferring)
- `AGENTS.md` documents the deployment method(s)
- Source code is untouched
- The project is ready for the first story

**Next steps for the user:**
1. Review the generated AGENTS.md and make any final adjustments
2. Create the first feature and stories
3. Start the dev-workflow with the first story
