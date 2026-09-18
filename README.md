# opencode Pipeline

**A multi-agent development pipeline as config-as-code** — for teams building software through structured dialogue, deterministic automation, and cheap-model mass work.

## Intro / Pitch

The opencode pipeline is a framework for **Requirements → Design → Stories → Dev (cheap model) → QA Gate** workflows. Everything is kept as flat, portable configuration (config-as-code), so you can clone it, adjust your local model assignment, and go.

### The four roles

The pipeline orchestrates four specialized agents:

- **Architect** (strong model) — conducts requirements interviews, designs the system, decomposes work into stories. Pure reasoning, dialogue-driven.
- **Developer** (cheap bulk model) — implements exactly one story per isolated Git branch. Many developers can run in parallel. Tests first, then code.
- **QA-Manager** (cheap model) — deterministic gatekeeper. Runs compressed test suites, checks architecture rules, returns JSON verdicts (PASS/FAIL/BLOCKED). Falls back to Architect only for unclear design issues.
- **Documenter** (cheap model) — reconciles documentation after QA-PASS. Synthesizes what exists; does not invent.

### What's inside

The repository contains:

- **`agent/`** — The four role definitions (architect, developer, qa-manager, documenter). Each is a Markdown file with frontmatter (description, mode, rules) and a prompt. Roles are portable; model assignment is local.
- **`scripts/`** — 15+ deterministic Python scripts + `qa_compress.sh` (Bash). Automation for worktree setup, story management, QA routing, session recovery, feature claiming, project scaffolding, architecture checks.
- **`plugins/`** — Pipeline enforcement plugin (TypeScript). Deterministic guards that block process violations: merge without QA-PASS, architect editing code, merge without documenter, session start without recovery. Deploys to `~/.config/opencode/plugins/` via release branch.
- **`templates/`** — Skeletons for new projects: `AGENTS.md` (project knowledge template) and `.gitignore`.
- **`command/`** — Invokable commands that orchestrate the flow: `/new-project`, `/requirements`, `/decompose`, `/implement`, `/qa-check`, `/status`, `/qa_summary`, `/document`.
- **`docs/features/`** — Hierarchical planning structure: features contain stories, stories contain developer targets and test criteria.
- **`.pipeline/`** — Persistent pipeline state: intent tracking (`intent.json`), QA verdicts (`qa-state/`).

### Design principles

1. **Cheap models for mass work** — Developer and QA-Manager run on lean models. Only the Architect (reasoning) and fallback diagnostics use strong models. This keeps costs low while maintaining quality gates.

2. **Deterministic scripts over LLM free-hand** — QA is not a thinker; it's a judge. Test compression (`qa_compress.sh`) reduces 20,000 lines of pytest spam to ≤200 tokens. Verdicts are strict JSON, no monologues.

3. **Config-as-code (clone & go)** — The entire framework is flat, readable files (Markdown + Bash). No secrets, no binary format. Transfer to another machine: clone, create local `opencode.jsonc`, restart. Done.

4. **Tests before code** — Every story has test criteria written before implementation. Tests use fake interfaces; no real external systems (Modbus, HA, APIs, Ollama) in the test suite.

5. **Function vs. connectivity separation** — Projects built with this pipeline follow a strict pattern:
   - `src/core/` — pure logic, zero imports from framework/IO/DB/API. Fully unit-testable.
   - `src/adapters/` — thin wrappers (3–10 lines) that read/write external interfaces and delegate to core.
   - Fake interfaces are mandatory for every external dependency.

### Important notes

- **`opencode.jsonc` is local, gitignored** — Provider endpoints, model names, and per-agent model assignment live in `~/.config/opencode/opencode.jsonc` on each machine. This file is not in the repository.
- **Per-agent model assignment** — The role files (`agent/*.md`) no longer carry a hardcoded `model:` line. Which model runs for which purpose is configured locally in the JSON under `agent`. Other machines have different providers/model names → only adjust the local JSON, the role files stay untouched.

---

## Development Process

This section explains the **practical "how"**: what you do as a user, what the agents do autonomously, and where the handoffs happen.

### Overview (Mermaid)

```mermaid
flowchart TD
    A["User: idea / requirement"] --> B["Phase 1: Design Dialogue\n(User ↔ Architect)"]
    B --> C["Architect outputs:\nrequirements.md\ndesign.md\nSTORIES.md + story files"]
    C --> D{"Phase 2: User-Go Checkpoint\n(Architect presents plan)"}
    D -- "User says 'go' / 'passt'" --> E["Phase 3: Autonomous Dev+QA"]
    D -- "User gives feedback" --> B

    E --> F["Developer implements story\n(tests first, isolated branch)"]
    F --> G["QA-Manager checks\n(qa_compress.sh → JSON verdict)"]
    G -- "PASS" --> H["Merge to main\n(after user clearance)"]
    G -- "FAIL (max 3×)" --> F
    G -- "BLOCKED_Design" --> I["Architect fixes design\n(autonomous, no user needed)"]
    I --> F
    G -- "BLOCKED_Requirements" --> J["Escalation to User\n(intent unclear)"]
    J --> B
```

### Phase 1: Design dialogue (User ↔ Architect)

You start by talking to the **Architect** — either via `/new-project` (new repo) or `/requirements` (existing repo). The Architect conducts an **iterative interview**: it asks about the problem, target audience, scope boundaries, and non-functional requirements. You answer, it refines, you correct — this is a back-and-forth dialogue.

**How to stay in the dialogue:** The Architect runs in `mode: all` (direct conversation partner). You talk to it like a colleague. It will ask clarifying questions — answer them. If it tries to spawn a Developer or QA-Manager prematurely, the **`permission.task` system** pops up an approval dialog (Tab key to confirm/deny). This is your hard technical gate — the Architect cannot silently start the machine.

**What the Architect produces:**
- `docs/requirements.md` — functional + non-functional requirements with REQ-IDs
- `docs/design.md` — architecture (function vs connectivity, fake interfaces, data model)
- `STORIES.md` + `docs/features/<feature>/stories/<phase>-<id>-<slug>.md` — decomposed, implementable stories with developer targets and test criteria

**Key principle:** Stories are cut small enough that a **cheap mass model** can implement each one in isolation on its own Git branch. No monster stories. The expensive/strong model (Architect) only reasons about design — it never writes code.

### Phase 2: User-Go checkpoint

Before any implementation starts, the Architect presents a **concrete implementation overview**:
- **WHAT:** which stories, which developer targets (exact scope — no more, no less)
- **HOW:** execution order (waves), which fakes are needed, test criteria per story

**You must give explicit approval** ("passt", "go", or similar). Without your go, nothing starts. If you have feedback, it flows back into planning (loop back to Phase 1), and the Architect presents a revised plan.

This checkpoint exists both as a **prompt rule** (behavioral) and as a **technical enforcement** via `permission.task` — even if the LLM "overhears" the prompt rule, the UI approval dialog catches it.

### Phase 3: Autonomous Dev+QA

Once you give the go, the pipeline runs **autonomously for a long time** without needing you:

1. **Developer** (cheap model) picks up a story, creates branch `feature/<story-id>-<slug>`, and works in its own Git worktree (`.worktrees/<story-id>-<slug>/`).
   - Reads the story's developer targets and test criteria
   - **Writes tests first** (using fake interfaces — no real external systems)
   - Implements exactly the developer targets in `src/core/` (pure logic) then `src/adapters/` (thin wrappers)
   - Runs `pytest` green, commits with metadata

2. **QA-Manager** (cheap model) checks the branch — **deterministically, not by thinking**:
   - Runs `qa_compress.sh` which compresses pytest output to ≤200 tokens (exit code + failed test names + assertions — no log spam)
   - Evaluates the compressed result against acceptance criteria
   - Checks architecture separation (no IO imports in core, fake parity, integration tests call real orchestration code)
   - Returns a **strict JSON verdict**: `{"status": "PASS|FAIL|BLOCKED_*", "reason": "...", "failed_tests": [...]}`

3. **On PASS** → branch is cleared for merge (you confirm the merge).

**Multiple stories can run in parallel** — each Developer works in its own worktree on its own branch. The QA-Manager checks each independently.

### Escalation paths (when things go wrong)

The pipeline has **hard autonomy limits** to prevent endless looping:

#### FAIL → Developer fix loop (max 3 rounds)

If QA returns FAIL, the Developer gets a **concrete fix assignment** (file, line, what's missing) and fixes on the same branch. QA checks again. This loops **at most 3 times** — if the story still fails after 3 rounds, it escalates to BLOCKED.

#### BLOCKED_Design → Architect repairs autonomously

If the failure is a **design gap** (test not simulatable, story wrongly cut, core/adapter separation undesigned), QA triggers the Architect with a lean 2-sentence diagnosis. The Architect fixes the design **minimally invasive** — no user needed for technical corrections. Then a new Dev round starts.

**Autonomy budget:** max 1–2 Architect design fixes per story. If the fix doesn't resolve it → escalation to user.

#### BLOCKED_Requirements → Back to you

If the failure is a **domain/intention question** (requirement unclear, behavior ambiguous, feature scope uncertain), QA escalates to you with a precise question. Only you know the intent — the pipeline never guesses.

### Quick reference (commands)

| Command | Agent | What it does |
|---|---|---|
| `/new-project` | Architect | Create new project + start requirements interview |
| `/requirements` | Architect | Start/continue requirements & design dialogue |
| `/decompose` | Architect | Break requirements into stories |
| `/implement <story-id>` | Developer | Implement one story (tests first, isolated branch) |
| `/qa-check <branch>` | QA-Manager | Run QA gate → JSON verdict (PASS/FAIL/BLOCKED) |
| `/status` | QA-Manager | Show implementation status (table: story, branch, tests, QA, error) |
| `/qa_summary` | — | Run `qa_compress.sh` and show compact test report |
| `/document [scope]` | Documenter | Reconcile documentation against code state |

---

## Installation

### Fresh install

If you're setting up opencode for the first time:

```bash
# Clone the repo to ~/.config/opencode (release branch = stable, default)
git clone git@github.com:bachmarc/opencode-pipeline.git ~/.config/opencode

# The default branch is 'release' (stable). If you want to contribute
# to development, switch to main:
#   git checkout main
```

Then restart `opencode` — agents, skills, commands are active.

### Existing setup

If you already have `~/.config/opencode` and want to add the framework:

```bash
cd ~/.config/opencode

# Initialize git and add the remote
git init
git remote add origin git@github.com:bachmarc/opencode-pipeline.git

# Fetch and check out the release branch
git fetch origin
git checkout -b release --track origin/release
```

**Important:** Local files (`opencode.jsonc`, `cron.db`) are gitignored, so this process preserves them. Your existing configuration stays intact.

### Local configuration (stays per machine)

Create `~/.config/opencode/opencode.jsonc` (e.g.):

```jsonc
{
  "$schema": "https://opencode.ai",
  "provider": { /* your model provider, e.g. Ollama via openai-compatible */ },
  "model": "provider/model",            // primary/dialogue model
  "small_model": "provider/model",      // lean model (titles, summaries)
  "agent": {                            // model per agent (architect/developer/qa-manager/documenter)
    "architect": {
      "model": "provider/strong",
      "reasoningEffort": "high",
      "permission": { "task": { "developer": "ask", "qa-manager": "ask" } }
    },
    "developer":   { "model": "provider/cheap", "reasoningEffort": "medium" },
    "qa-manager":  { "model": "provider/cheap", "reasoningEffort": "high"   },
    "documenter":  { "model": "provider/cheap", "reasoningEffort": "low"    }
  },
  "skills": { "paths": ["~/.config/opencode/skills"] }
}
```

> **Do not** commit this here — it's in `.gitignore`, because host/provider differ per machine.
>
> **Reasoning depth (`reasoningEffort`)** is set per agent and controls how hard the model thinks before answering. Values: `low`, `medium`, `high` (unset = model default). Like model assignment, it stays in the local file and is not committed. Different machines can tune reasoning depth independently.

Then restart `opencode` — the config is loaded at startup; changes are not hot-reloaded.

**For details on model assignment, see [Model Assignment](#model-assignment) below. For Phase-0 enforcement, see [Phase-0 Checkpoint](#phase-0-checkpoint) below.**

---

## Technical Details

This section is a reference for deeper topics. Links from the Installation section above point here.

### <a id="model-assignment"></a>Model Assignment

The four role files (`agent/architect.md`, `developer.md`, `qa-manager.md`, `documenter.md`) no longer set a model (previously hardcoded as `model:`). Instead there's a **separation: role vs. machine**:

- **Role (portable, in Git):** *who does what* — mode, temperature, prompt, rules. In `agent/*.md`.
- **Machine (local, gitignored):** *which model* for *what*. In `~/.config/opencode/opencode.jsonc` under `agent`.

**Why:**
- Other machines have different APIs/providers wired up and different model names. When the model was hardcoded in the role file, the role core had to be touched.
- Now a **single local file** (`opencode.jsonc`) suffices — provider endpoints, model names **and** the `agent` assignment. On a clone on a new machine you only create/adjust this file; the roles stay identical.

**Concrete procedure per machine:**
1. `git clone git@github.com:bachmarc/opencode-pipeline.git ~/.config/opencode`
2. Create `opencode.jsonc` (see above) with your provider + the `agent` mapping entries matching your available models.
3. Restart `opencode` — the config is loaded at startup; changes are not hot-reloaded.
4. If a mapping entry is missing, opencode does not fail: an agent without an assigned model falls back to the global `model` as default.

**Reasoning depth: `reasoningEffort`**

Model choice and reasoning depth are two separate tuning axes on the same model. A cheap model with `"reasoningEffort": "high"` reasons more carefully than the same model at `"low"`. The pipeline's rationale: developer at medium (repetitive implementation benefits from speed), qa-manager at high (verdicts require scrutiny — wrong PASS is worse than slow PASS), documenter at low (mechanical reconciliation), architect unset (strong model's default reasoning is sufficient).

### <a id="phase-0-checkpoint"></a>Phase-0 Checkpoint Enforcement

The rule "no dev/QA without explicit user-go" lives in the prompts — but an LLM follows instructions probabilistically and can "overhear" them. The fix: opencode's `permission.task` system. When the architect tries to spawn a developer or qa-manager, a **UI approval dialog pops up for you** — every time. Your "allow" click **is** the user-go, technically enforced. The architect cannot silently start the machine.

```jsonc
"agent": {
  "architect": {
    "permission": { "task": { "developer": "ask", "qa-manager": "ask" } }
  }
}
```

- The prompt rules stay as behavioral training, but the hard guarantee comes from the permission system.
- Internal QA loops (QA → developer on FAIL fixes) are intentionally **not** gated — that autonomy should remain, since the wave was already started by you.
- This block belongs in the local `opencode.jsonc` (it's config, not a role), so it travels with the model assignment on every machine.

### The four agents in detail

| | architect | developer | qa-manager | documenter |
|---|---|---|---|---|
| **Role** | Requirements-/Design-/Story partner, dialogue | Cheap story implementer | Deterministic gatekeeper | Documentation consistency |
| **Model** | strong | cheap bulk | cheap (+ strong fallback via architect) | cheap |
| **Reasoning depth** | high (deep design reasoning) | medium (speed over depth) | high (verdicts need scrutiny) | low (mechanical reconciliation) |
| **Model source** | `opencode.jsonc` → `agent.architect.model` | `opencode.jsonc` → `agent.developer.model` | `opencode.jsonc` → `agent.qa-manager.model` | `opencode.jsonc` → `agent.documenter.model` |
| **Mode** | `all` (dialogue) | `subagent` | `all` | `subagent` |
| **Output** | Docs / Stories | Branch + commit | JSON (`PASS/FAIL/BLOCKED_*`) | Updated docs + docstrings |
| **Budget** | — | 1 story = 1 branch | max. 3 FAIL loops, then escalation | after QA-PASS, before merge |

### Deployment (dev repo → live config)

#### Branching strategy

The repository uses a **two-branch deployment model**:

- **`main` branch** — development line. Stories are developed and merged here after the QA gate. May be unstable between milestones.
- **`release` branch** — stable, deployable state. Promoted from `main` only when the user considers the code production-ready. The live clone (`~/.config/opencode`) pulls from `release`, not `main`.

#### Promotion workflow

When `main` is stable enough for production, promote it to `release` using the `promote_release.py` script:

```bash
python scripts/promote_release.py
```

This script:
1. Validates that `main` is clean and up-to-date with remote
2. Fast-forward merges `release` to current `main` HEAD
3. Pushes `release` to remote
4. Outputs JSON with promotion status and commit hashes
5. Returns exit code 0 on success, 1 on dirty state or if behind remote

#### Live clone deployment

The **live clone** (`~/.config/opencode`) pulls from the `release` branch, not `main`:

```bash
git -C ~/.config/opencode pull origin release
```

Then **restart opencode** — the config is loaded once at startup, there is no hot-reload. Running sessions keep using the old config until they are restarted.

**What a pull does not touch:** `opencode.jsonc` and `cron.db` are gitignored, so a pull never overwrites them. New agent-/command-/skill-/template files appear automatically after pull + restart.

**Versioning:** `APP_VERSION` (in `APP_VERSION.py` at the repo root) — bump on notable merges, documented in STORIES.md.

**New config options:** if a release introduces new `opencode.jsonc` options (e.g. the `permission.task` block), **every machine** must add them to its local file once — see § "Model Assignment" above for the per-machine procedure.

**Rollback:** check out a known-good version in the live clone and restart opencode:

```bash
git -C ~/.config/opencode checkout <tag-or-hash>
```

**No deploy script — by design:** deployment stays deliberately manual (staged rollout; the framework steers the running agent). Optional convenience later, manual is the default.

### Extending: new test processes (`qa_compress.sh` is modular)

`qa_compress.sh` uses a **checker-registry pattern with plugin files**. Each test process lives in its own file in `scripts/qa_checkers/` and registers itself. Available checkers: `pytest` (default), `rspec` (Ruby), `jest` (JavaScript), `gradle` / `maven` (Java), `json` / `yaml` (syntax validation), `html` (simple syntax check).

```bash
# scripts/qa_checkers/mypy.sh — one file per checker
mypy_check() { mypy "$@" >/dev/null 2>&1; return $?; }
register_check mypy mypy_check
```

Which checkers actually run is declared per project in `qa_config.json` (in the project cwd): `{"checkers": ["pytest", "mypy"]}`. Missing file → default `["pytest"]`; invalid JSON → loud fail; unknown checker name → loud FAIL; empty list → explicit opt-out (PASS). Aggregation (overall FAIL as soon as one checker is non-zero) and exit code happen automatically. New checkers = one plugin file + registration line. See feature: polyglot-qa, stories: 12-01-qa-config-contract, 12-02-checker-rspec-jest, 12-03-checker-gradle-maven, 12-04-checker-json-yaml.

### Per-project AGENTS.md (project knowledge, per repo)

Every project repo carries its own `AGENTS.md` — loaded via `"instructions": ["AGENTS.md"]` as context into **every session of every agent** working in that folder. It is not the agents' definition (that lives here, in `agent/*.md`); it is the **project's knowledge**: stack, core rules, architecture separation, git conventions, references.

- **Agent definition (global, this repo):** who the agent is, prompt, behavior — identical on every machine.
- **Project AGENTS.md (per repo, in the project):** what the project is and which rules its code must follow — versioned with the code, correct on every checkout.

**Template:** `templates/AGENTS.md` provides the skeleton. Constant sections (workflow, git conventions, languages, prohibitions) are the binding interface between framework and project and stay untouched; project-specific placeholders (`name`, stack, core rules, references) are filled in dialogue. The architect must use the template — no improvising from zero.

### Architecture pattern projects must follow

The actual pattern behind everything is **function vs. connectivity**:

- `src/core/` — pure logic/rules, **zero imports** from framework/IO/DB/API. Gets everything as parameters, returns dicts/primitives. Fully unit-testable.
- `src/adapters/` — **thin wrappers** (3–10 lines): read/write external interfaces, delegate decisions to core.
- **Fake interfaces are mandatory** for every external dependency → tests run without real systems.

Therefore: **tests exist BEFORE the code**, each story has its own fake-based test criteria.

---

## Open points / outlook

- `qa_compress.sh` is verified against **pytest 9** (PASS: `78 passed`; FAIL: `2 failed, 1 passed`); for older pytest versions check one line in the summary grep if needed.
- Optional: merge into a shared `~/dotfiles` repo with other tools (then via symlink instead of a direct clone).
