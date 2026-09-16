# opencode Pipeline

Multi-agent development pipeline for folder projects: **Requirements → Design → Stories → Dev (cheap model) → QA Gate**. Everything kept as flat, portable opencode config (config-as-code).

> **Heads-up:** This repository intentionally contains **no `opencode.jsonc`** (provider endpoints, model selection) and **no `cron.db`** (local state). Both stay **local** per machine and are gitignored here.

> **Per-agent model assignment:** The roles (`agent/*.md`) no longer carry a hardcoded `model:` line. Which model runs for which purpose is configured **locally in the JSON** under `agent` (see § "Model assignment in the JSON"). Other machines have different providers/model names → only adjust the local JSON, the role files stay untouched.

---

## What's inside — and why

| Folder | Contents | Why |
|---|---|---|
| `agent/` | `architect`, `developer`, `qa-manager` | The three pipeline roles as opencode agents |
| `skills/dev-workflow/` | `SKILL.md` | The complete, reusable development workflow |
| `scripts/` | `qa_compress.sh` | Deterministic pytest compression for the QA gate |
| `command/` | `qa_summary`, `qa-check`, `status`, `new-project`, `requirements`, `decompose`, `implement` | Invokable commands that orchestrate the flow |

The goal is a **lean, cheap, autonomously running multi-agent system** — no nested LLM cascades that burn tokens.

---

## Design decisions behind it (the "why")

### 1. Separation of functions: Architect thinks, Developer writes, QA checks

- **architect** (strong) — talks Requirements/Design/Stories out in dialogue. Pure reasoning.
- **developer** (cheap bulk model) — implements **exactly one story** isolated per branch. Many in parallel.
- **qa-manager** (cheap model) — **deterministic judge**, not a thinker. Strong model only as **fallback** via `architect` for unclear error/design causes.

### 2. The three efficiency levers (core of the "why")

1. **Streamline & offload QA** — cost dampener
   - pytest logs are **deterministically compressed** (`qa_compress.sh`, ≤200 tokens instead of 20 000 log spam). **Evaluating pytest does not need a big model.**
   - QA output is **strictly JSON-only** (`status | reason | failed_tests`), no monologues, no style chit-chat.
   - Cheap model for the QA judge; the expensive model only for unclear causes.

2. **Break the cascade** — against context bloat
   - `BLOCKED_Design` → **stays autonomous**: QA delegates root-cause analysis to `architect` with a lean diagnosis (2 sentences + compressed test list, **no log spam**).
   - `BLOCKED_Requirements` → **escalate to the user** (only the user knows the intent).
   - No automatic architect-dispatch from QA. Results are **passed through 1:1**, nothing reformulated.

3. **Autonomy with hard limits**
   - The process runs a long time **without user interaction** (dev waves, QA, design repair).
   - **Autonomy budget:** max. 3 developer FAIL loops + max. 1–2 architect design fixes per story. If both run dry → **BLOCKED_Requirements to user** (no endless looping).
   - **Phase-0 checkpoint:** before every dev/QA start the architect presents the plan; only **explicit user-go** starts the machine — except for purely technical design corrections.

### 3. Architecture of the projects this pipeline builds (from the workflow)

The actual pattern behind everything is **function vs. connectivity**:

- `src/core/` — pure logic/rules, **zero imports** from framework/IO/DB/API. Gets everything as parameters, returns dicts/primitives. Fully unit-testable.
- `src/adapters/` — **thin wrappers** (3–10 lines): read/write external interfaces, delegate decisions to core.
- **Fake interfaces are mandatory** for every external dependency → tests run without real systems.

Therefore: **tests exist BEFORE the code**, each story has its own fake-based test criteria.

### 4. Why config-as-code / Git

- The whole pipeline is only **flat, readable files** (Markdown + a portable bash script). No secrets, no binary format.
- Thus **transferable to other machines / other opencode installs**: clone, done. The exec bit of `qa_compress.sh` is preserved via Git.
- **No secrets** in the config → safe to commit.
- The only machine-specific part (`opencode.jsonc`) stays deliberately local.

---

## Installation on another machine

```bash
# 1. Clone the repo to where opencode expects its config
#    (if ~/.config/opencode already exists: back it up / empty it first)
git clone git@github.com:bachmarc/opencode-pipeline.git ~/.config/opencode

# 2. Create LOCKALLY per machine (not in the repo!): opencode.jsonc
#    with provider endpoint (e.g. Ollama baseURL) + model selection.
#    Template below under "Local configuration".
```

Then restart `opencode` — agents, skills, commands are active.

### Local configuration (stays per machine)

Create `~/.config/opencode/opencode.jsonc` (e.g.):

```jsonc
{
  "$schema": "https://opencode.ai",
  "provider": { /* your model provider, e.g. Ollama via openai-compatible */ },
  "model": "provider/model",            // primary/dialogue model
  "small_model": "provider/model",      // lean model (titles, summaries)
  "agent": {                            // model per agent (architect/developer/qa-manager)
    "architect": {
      "model": "provider/strong",
      "permission": { "task": { "developer": "ask", "qa-manager": "ask" } }
    },
    "developer":   { "model": "provider/cheap"   },
    "qa-manager":  { "model": "provider/cheap"   }
  },
  "skills": { "paths": ["~/.config/opencode/skills"] }
}
```

> **Do not** commit this here — it's in `.gitignore`, because host/provider differ per machine.

### How model assignment works ("the JSON procedure")

The three role files (`agent/architect.md`, `developer.md`, `qa-manager.md`) no longer set a model (previously hardcoded as `model:`). Instead there's a **separation: role vs. machine**:

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

### Enforcing the Phase-0 checkpoint technically (not just via prompt)

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

---

## Workflow in 60 seconds

1. **New project:** `/new-project` → Architect interview (Requirements, Design, Stories) in dialogue, **review checkpoint with user-go**.
2. **Implement:** `/implement <story-id>` (Developer) — tests first, isolated branch.
3. **QA gate:** `/qa-check <branch>` (QA-Manager) → `qa_compress.sh` compresses pytest → JSON review.
4. **Status:** `/status` (QA-Manager, table Story | Branch | Tests | QA | Error).
5. **Compact QA test report:** `/qa_summary`.

---

## The three agents in detail

| | architect | developer | qa-manager |
|---|---|---|---|
| **Role** | Requirements-/Design-/Story partner, dialogue | Cheap story implementer | Deterministic gatekeeper |
| **Model** | strong | cheap bulk | cheap (+ strong fallback via architect) |
| **Model source** | `opencode.jsonc` → `agent.architect.model` | `opencode.jsonc` → `agent.developer.model` | `opencode.jsonc` → `agent.qa-manager.model` |
| **Mode** | `all` (dialogue) | `subagent` | `all` |
| **Output** | Docs / Stories | Branch + commit | JSON (`PASS/FAIL/BLOCKED_*`) |
| **Budget** | — | 1 story = 1 branch | max. 3 FAIL loops, then escalation |

---

## Extending: new test processes (`qa_compress.sh` is modular)

`qa_compress.sh` uses a **checker-registry pattern**. Each test process (pytest, ruff, mypy, …) is a function that writes its compressed result to stdout and returns its subprocess's exit code.

```bash
# 1. Define a new checker function
mypy_check() { mypy "$@" >/dev/null 2>&1; return $?; }

# 2. Register (activate) it
register_check mypy mypy_check
```

Aggregation (overall FAIL as soon as one checker is non-zero) and exit code happen automatically. Future test processes = one function + one registration line.

---

## Open points / outlook

- `qa_compress.sh` is verified against **pytest 9** (PASS: `78 passed`; FAIL: `2 failed, 1 passed`); for older pytest versions check one line in the summary grep if needed.
- Optional: merge into a shared `~/dotfiles` repo with other tools (then via symlink instead of a direct clone).
