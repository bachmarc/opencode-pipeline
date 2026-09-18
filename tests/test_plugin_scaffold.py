"""Tests for plugin scaffold — TypeScript plugin infrastructure."""

from pathlib import Path


def test_plugin_file_exists():
    """plugins/pipeline-enforcement.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    assert plugin_file.exists(), f"Plugin file not found at {plugin_file}"


def test_package_json_exists():
    """plugins/package.json exists and contains @opencode-ai/plugin."""
    repo_root = Path(__file__).resolve().parent.parent
    package_json = repo_root / "plugins" / "package.json"
    assert package_json.exists(), f"package.json not found at {package_json}"
    
    content = package_json.read_text()
    assert "@opencode-ai/plugin" in content, "package.json missing @opencode-ai/plugin dependency"


def test_plugin_exports_named_function():
    """plugins/pipeline-enforcement.ts exports PipelineEnforcement."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "PipelineEnforcement" in content, "PipelineEnforcement not found in plugin file"
    assert "export" in content, "export keyword not found in plugin file"


def test_plugin_has_tool_hook():
    """plugins/pipeline-enforcement.ts contains tool.execute.before hook."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "tool.execute.before" in content, "tool.execute.before hook not found in plugin file"
