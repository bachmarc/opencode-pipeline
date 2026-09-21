---
description: Guide Architect through 6-phase project migration workflow
mode: skill
---

# migrate-project Skill — 6-Phase Migration Workflow

This skill guides the Architect through migrating an existing project into the opencode pipeline framework. The migration is deterministic and non-destructive — it analyzes the project, generates configuration files, and provisions missing structure without modifying source code.

## Phase 1: Analyze Project Structure

Run the project analyzer to understand the current state:

```bash
python scripts/analyze_project.py <path>
```

This script:
- Scans the project directory for existing structure (git, source code, tests, docs)
- Detects the main branch name (main, master, develop, etc.)
- Identifies the tech stack (Python, TypeScript, Go, etc.)
- Returns JSON analysis with project metadata

**Output:** JSON object with keys like `project_name`, `main_branch`, `tech_stack`, `has_git`, `has_src`, `has_tests`, `existing_agents_md`, etc.

## Phase 2: Present Analysis & Confirm Stack

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

3. **Extract existing AGENTS.md content (if present):**
   - If the project already has an AGENTS.md file, read it
   - Extract project-specific sections (stack, core rules, architecture notes)
   - These will be used in Phase 3 to preserve existing context

## Phase 3: Interactive AGENTS.md Generation

Generate the AGENTS.md file for the project:

1. **Use the prepare_agents_md.py script to create a draft:**
   ```bash
   python scripts/prepare_agents_md.py <path> --existing-agents <path-to-existing-agents-if-any>
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
python scripts/provision_structure.py <path>
```

This script:
- Creates missing directories: `docs/features/`, `STORIES.md`, `tests/fakes/`, `.pipeline/`, etc.
- Creates template files: `docs/features/_feature_template.md`, `docs/features/_story_template.md`
- Creates `.gitignore` if missing
- Creates `README.md` skeleton if missing
- Does NOT overwrite existing files

**Output:** List of created directories and files.

## Phase 5: Optional Retro Stories (User Choice)

Ask the user if they want to create "retro stories" for existing work:

1. **Ask the user:**
   - "Would you like to create retro stories for existing work? (yes/no)"
   - If yes: "How granular? (fine-grained: one story per feature, coarse: one story per major phase)"

2. **If user chooses yes, run the retro stories script:**
   ```bash
   python scripts/create_retro_stories.py <path> --granularity <fine|coarse>
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
python scripts/validate_migration.py <path>
```

This script:
- Checks that all required files exist (AGENTS.md, STORIES.md, docs/features/, tests/fakes/, etc.)
- Validates AGENTS.md frontmatter and structure
- Checks that git is initialized
- Verifies that source code was not modified
- Returns a validation report

**Output:** Validation report with status (PASS/FAIL) and any issues found.

## Summary

After all 6 phases:
- The project has a complete opencode pipeline structure
- AGENTS.md is configured for the project
- All required directories and templates exist
- Source code is untouched
- The project is ready for the first story

**Next steps for the user:**
1. Review the generated AGENTS.md and make any final adjustments
2. Create the first feature and stories
3. Start the dev-workflow with the first story
