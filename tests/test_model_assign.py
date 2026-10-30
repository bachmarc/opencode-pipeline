"""Tests for scripts/model_assign.py (Story 31-01).

Deterministic tier-to-model appliance: reads a role map JSON and patches the
local opencode config's agent.<role>.model lines. The official OpenCode v2
config key is "agent" (singular); the legacy "agents" (plural) key is patched
as a deterministic fallback, and a config carrying BOTH keys is refused as
ambiguous. All tests are hermetic — they pass explicit --map/--config flags
pointing at fixture files in tmp_path. No external systems, no HOME fiddling.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPT = REPO_ROOT / "scripts" / "model_assign.py"

# --- fixtures ------------------------------------------------------------------

CONFIG_BEFORE = """{
  "$schema": "https://opencode.ai/config.json",

  // provider block — untouched by the patcher
  "provider": {
    "fake-provider": {
      "models": {
        "fake-model-a": { "tools": true }
      }
    }
  },

  "agent": {
    "architect": {
      "model": "fake-provider/fake-model-a",
      "reasoningEffort": "high"
    },
    "developer": {
      // a comment between keys must survive
      "model": "fake-provider/fake-model-b",
      "reasoningEffort": "high"
    },
    "qa-manager": {
      "model": "fake-provider/fake-model-c",
      "reasoningEffort": "low"
    }
  }
}
"""

MAP = {
    "architect": {"tier": "strong", "provider_model": "fake-provider/fake-model-x"},
    "developer": {"tier": "cheap", "provider_model": "fake-provider/fake-model-y"},
    "qa-manager": {"tier": "cheap", "provider_model": "fake-provider/fake-model-z"},
}


def write_fixtures(
    tmp_path: Path, config_text: str = CONFIG_BEFORE, map_data: dict | None = MAP
) -> tuple[Path, Path]:
    """Create fixture map and config files; return (map_path, config_path)."""
    map_path = tmp_path / "model_map.json"
    config_path = tmp_path / "opencode.jsonc"
    map_path.write_text(json.dumps(map_data, indent=2), encoding="utf-8")
    config_path.write_text(config_text, encoding="utf-8")
    return map_path, config_path


def run_script(args: list[str]) -> tuple[int, str, str]:
    """Run model_assign.py with the given args. Returns (exit, stdout, stderr)."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)] + args,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


# --- --apply -------------------------------------------------------------------


def test_apply_patches_model_lines(tmp_path: Path) -> None:
    """Only agent.<role>.model lines change; every other line stays byte-identical."""
    map_path, config_path = write_fixtures(tmp_path)

    exit_code, stdout, stderr = run_script(
        ["--apply", "--map", str(map_path), "--config", str(config_path)]
    )
    assert exit_code == 0, f"apply failed: {stderr}"

    result = json.loads(stdout)
    assert result["result"] == "PASS"
    assert result["applied"] == {
        "architect": {
            "model": "fake-provider/fake-model-x",
            "key": "agent",
        },
        "developer": {
            "model": "fake-provider/fake-model-y",
            "key": "agent",
        },
        "qa-manager": {
            "model": "fake-provider/fake-model-z",
            "key": "agent",
        },
    }

    after_lines = config_path.read_text(encoding="utf-8").splitlines()
    before_lines = CONFIG_BEFORE.splitlines()
    assert len(after_lines) == len(before_lines), "line count must not change"

    changed: list[str] = []
    for before, after in zip(before_lines, after_lines):
        if before == after:
            continue
        # only model lines may differ — assert the shape of each change
        assert '"model"' in before, f"non-model line changed: {before!r}"
        changed.append(before)
        assert after.startswith(before.split('"model"')[0] + '"model"')
    assert sorted(changed) == sorted(
        line for line in before_lines if '"model"' in line
    ), "every model line must be patched, nothing else"

    # comments survive byte-identical
    comment_lines = [l for l in before_lines if l.strip().startswith("//")]
    for line in comment_lines:
        assert line in after_lines, f"comment lost: {line!r}"

    # the new values actually landed
    text_after = config_path.read_text(encoding="utf-8")
    assert '"model": "fake-provider/fake-model-x"' in text_after
    assert '"model": "fake-provider/fake-model-y"' in text_after
    assert '"model": "fake-provider/fake-model-z"' in text_after
    assert '"model": "fake-provider/fake-model-a"' not in text_after


def test_apply_refuses_ambiguous(tmp_path: Path) -> None:
    """Two model keys in one role block -> exit 1, file bytes unchanged."""
    ambiguous = CONFIG_BEFORE.replace(
        '      "model": "fake-provider/fake-model-b",',
        '      "model": "fake-provider/fake-model-b",\n      "model": "fake-provider/fake-model-b2",',
    )
    map_path, config_path = write_fixtures(tmp_path, config_text=ambiguous)
    before_bytes = config_path.read_bytes()

    exit_code, stdout, stderr = run_script(
        ["--apply", "--map", str(map_path), "--config", str(config_path)]
    )
    assert exit_code == 1, f"expected exit 1, got {exit_code}; stdout={stdout}"
    assert stderr.strip(), "an error message is expected on stderr"
    assert config_path.read_bytes() == before_bytes, "file must be untouched"


def test_apply_skips_missing_roles(tmp_path: Path) -> None:
    """Map role not present in config's agent object -> reported as skipped, exit 0."""
    map_data = dict(MAP)
    map_data["documenter"] = {"tier": "cheap", "provider_model": "fake-provider/fake-model-d"}
    map_path, config_path = write_fixtures(tmp_path, map_data=map_data)
    before_bytes = config_path.read_bytes()

    exit_code, stdout, stderr = run_script(
        ["--apply", "--map", str(map_path), "--config", str(config_path)]
    )
    assert exit_code == 0, f"apply failed: {stderr}"

    result = json.loads(stdout)
    assert result["result"] == "PASS"
    assert result["skipped"] == ["documenter"]
    assert set(result["applied"]) == {"architect", "developer", "qa-manager"}
    assert all(
        entry["key"] == "agent" for entry in result["applied"].values()
    )
    assert config_path.read_bytes() != before_bytes, "present roles must be patched"


def test_apply_patches_legacy_agents_key(tmp_path: Path) -> None:
    """Legacy 'agents' (plural) only config -> patched there; key field is 'agents'."""
    map_path, config_path = write_fixtures(
        tmp_path, config_text=CONFIG_BEFORE.replace('"agent": {', '"agents": {')
    )

    exit_code, stdout, stderr = run_script(
        ["--apply", "--map", str(map_path), "--config", str(config_path)]
    )
    assert exit_code == 0, f"apply failed: {stderr}"

    result = json.loads(stdout)
    assert result["result"] == "PASS"
    assert all(
        entry["key"] == "agents" for entry in result["applied"].values()
    ), "legacy plural key must be reported"
    assert result["applied"]["architect"] == {
        "model": "fake-provider/fake-model-x",
        "key": "agents",
    }
    text_after = config_path.read_text(encoding="utf-8")
    assert '"model": "fake-provider/fake-model-x"' in text_after


def test_apply_refuses_both_keys(tmp_path: Path) -> None:
    """Config with BOTH 'agent' and 'agents' objects -> exit 1, bytes unchanged."""
    ambiguous = CONFIG_BEFORE.replace(
        '  "provider": {',
        '  "agents": {\n    "architect": {\n      "model": "fake-provider/fake-model-old"\n    }\n  },\n  "provider": {',
    )
    map_path, config_path = write_fixtures(tmp_path, config_text=ambiguous)
    before_bytes = config_path.read_bytes()

    exit_code, stdout, stderr = run_script(
        ["--apply", "--map", str(map_path), "--config", str(config_path)]
    )
    assert exit_code == 1, f"expected exit 1, got {exit_code}; stdout={stdout}"
    assert stderr.strip(), "an error message is expected on stderr"
    assert config_path.read_bytes() == before_bytes, "file must be untouched"


# --- --show --------------------------------------------------------------------


def test_show_prints_map_json(tmp_path: Path) -> None:
    """--show on a valid fixture map prints exactly the mapping JSON, exit 0."""
    map_path, _ = write_fixtures(tmp_path)

    exit_code, stdout, stderr = run_script(["--show", "--map", str(map_path)])
    assert exit_code == 0, f"show failed: {stderr}"
    assert json.loads(stdout) == MAP


def test_show_missing_map_exits_1(tmp_path: Path) -> None:
    """--show with missing map -> exit 1 and a hint pointing at --init."""
    exit_code, stdout, stderr = run_script(
        ["--show", "--map", str(tmp_path / "does_not_exist.json")]
    )
    assert exit_code == 1
    assert "--init" in stderr, "missing map must hint at --init"


# --- --init --------------------------------------------------------------------


def test_init_creates_minimal_map(tmp_path: Path) -> None:
    """--init writes a minimal map (generic roles, tier cheap, empty model);
    a second run exits 1 without overwriting."""
    map_path = tmp_path / "model_map.json"

    exit_code, stdout, stderr = run_script(["--init", "--map", str(map_path)])
    assert exit_code == 0, f"init failed: {stderr}"

    created = json.loads(map_path.read_text(encoding="utf-8"))
    assert set(created) == {"architect", "developer", "qa-manager"}
    for entry in created.values():
        assert entry == {"tier": "cheap", "provider_model": ""}

    # second run must refuse (no silent overwrite)
    before_bytes = map_path.read_bytes()
    exit_code, stdout, stderr = run_script(["--init", "--map", str(map_path)])
    assert exit_code == 1, "second --init must exit 1"
    assert stderr.strip()
    assert map_path.read_bytes() == before_bytes, "existing map must not be touched"


# --- role abstraction self-check -----------------------------------------------


def test_no_model_names_in_script() -> None:
    """The script source contains no concrete model/provider names (role abstraction).

    Only generic role names are allowed. Checked against the same forbidden
    patterns the framework self-check uses for portable files.
    """
    source = SCRIPT.read_text(encoding="utf-8")
    forbidden = (
        "glm-",
        "deepseek",
        "qwen",
        "haiku",
        "claude-",
        "ollama",
        "openrouter",
        "anthropic",
        "minimax",
        "kimi",
        ":cloud",
        "gemini",
        "gpt-",
    )
    lowered = source.lower()
    for pattern in forbidden:
        assert pattern not in lowered, (
            f"model_assign.py must not name concrete models/providers "
            f"(found {pattern!r})"
        )
