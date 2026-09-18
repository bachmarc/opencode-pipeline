"""Tests for polyglot import checking in check_architecture.py (story 12-10).

Runs scripts/check_architecture.py via subprocess against tmp_path src/core
directories containing JS/TS/Ruby/Java files. Existing Python behavior is
pinned by tests/test_check_scripts.py and must stay green unchanged.
"""

import json
import subprocess
import sys
from pathlib import Path

SCRIPT = (
    Path(__file__).parent.parent / "scripts" / "check_architecture.py"
)


def run_check(core_dir: Path, allowlist: Path | None = None):
    """Run check_architecture.py via subprocess and return (returncode, output)."""
    cmd = [sys.executable, str(SCRIPT), str(core_dir)]
    if allowlist is not None:
        cmd += ["--allowlist", str(allowlist)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    assert result.stdout.strip(), f"No JSON on stdout: {result.stderr}"
    output = json.loads(result.stdout)
    return result.returncode, output


# --- JS / TS -------------------------------------------------------------


def test_js_clean(tmp_path):
    """JS with node builtin + relative import -> PASS, files_checked: 1."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "board.js").write_text(
        "import path from 'path';\n"
        "import { helper } from './helper.js';\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 0
    assert output["result"] == "PASS"
    assert output["files_checked"] == 1


def test_js_forbidden(tmp_path):
    """JS importing axios -> FAIL, violation contains axios and file."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "api.js").write_text("import axios from 'axios';\n", encoding="utf-8")
    code, output = run_check(core)
    assert code == 1
    assert output["result"] == "FAIL"
    violations = output["violations"]
    assert len(violations) == 1
    violation = violations[0]
    assert violation["import"] == "axios"
    assert "api.js" in violation["file"]
    assert "line" in violation
    assert violation["line"] >= 1


def test_js_require_form(tmp_path):
    """require('fs') passes, require('mongoose') fails."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "old.js").write_text(
        "const fs = require('fs');\n"
        "const db = require('mongoose');\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 1
    violations = output["violations"]
    assert len(violations) == 1
    assert violations[0]["import"] == "mongoose"
    assert "old.js" in violations[0]["file"]


def test_ts_file_checked(tmp_path):
    """TS file with relative + node builtin import -> PASS."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "board.ts").write_text(
        "import { Board } from './types';\n"
        "import http from 'http';\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 0
    assert output["result"] == "PASS"
    assert output["files_checked"] == 1


# --- Ruby ---------------------------------------------------------------


def test_ruby_clean_and_relative(tmp_path):
    """Ruby stdlib require + require_relative -> PASS."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "board.rb").write_text(
        "require 'json'\n"
        "require_relative 'cell'\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 0
    assert output["result"] == "PASS"
    assert output["files_checked"] == 1


def test_ruby_forbidden(tmp_path):
    """require 'sinatra' -> FAIL, violation contains sinatra."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "app.rb").write_text("require 'sinatra'\n", encoding="utf-8")
    code, output = run_check(core)
    assert code == 1
    violations = output["violations"]
    assert len(violations) == 1
    assert violations[0]["import"] == "sinatra"


# --- Java ---------------------------------------------------------------


def test_java_clean(tmp_path):
    """java.* import -> PASS."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "Board.java").write_text(
        "import java.util.List;\n"
        "\n"
        "class Board {\n"
        "}\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 0
    assert output["result"] == "PASS"
    assert output["files_checked"] == 1


def test_java_forbidden(tmp_path):
    """org.springframework import -> FAIL, contains org.springframework."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "Service.java").write_text(
        "import org.springframework.stereotype.Service;\n",
        encoding="utf-8",
    )
    code, output = run_check(core)
    assert code == 1
    violations = output["violations"]
    assert len(violations) == 1
    # Regex extracts the full package; the story requires it to contain
    # the forbidden prefix 'org.springframework'.
    assert "org.springframework" in violations[0]["import"]


# --- Mixed languages ----------------------------------------------------


def test_mixed_language_dir(tmp_path):
    """Clean .py + violating .js in one dir -> FAIL with exactly the js violation."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "board.py").write_text(
        "import sys\nimport os\n",
        encoding="utf-8",
    )
    (core / "api.js").write_text("import axios from 'axios';\n", encoding="utf-8")
    code, output = run_check(core)
    assert code == 1
    violations = output["violations"]
    assert len(violations) == 1
    assert violations[0]["import"] == "axios"
    assert "api.js" in violations[0]["file"]
    assert output["result"] == "FAIL"


# --- Custom allowlist ---------------------------------------------------


def test_allowlist_unlocks_js_module(tmp_path):
    """--allowlist containing 'axios' unlocks the JS import."""
    core = tmp_path / "src" / "core"
    core.mkdir(parents=True)
    (core / "api.js").write_text("import axios from 'axios';\n", encoding="utf-8")
    allowlist = tmp_path / "allowlist.txt"
    allowlist.write_text("axios\n", encoding="utf-8")
    code, output = run_check(core, allowlist=allowlist)
    assert code == 0
    assert output["result"] == "PASS"