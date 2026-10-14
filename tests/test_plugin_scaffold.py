"""Tests for plugin scaffold — TypeScript plugin infrastructure.

V2 plugin entrypoint tests: Verify pipeline-enforcement.ts conforms to V2 plugin API
(export default Plugin.define, @opencode/plugin import, execute.before hook registration).
"""

from pathlib import Path


def test_plugin_file_exists():
    """plugins/pipeline-enforcement.ts exists."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    assert plugin_file.exists(), f"Plugin file not found at {plugin_file}"


def test_package_json_exists():
    """plugins/package.json exists and contains @opencode/plugin (V2)."""
    repo_root = Path(__file__).resolve().parent.parent
    package_json = repo_root / "plugins" / "package.json"
    assert package_json.exists(), f"package.json not found at {package_json}"
    
    content = package_json.read_text()
    assert "@opencode/plugin" in content, "package.json missing @opencode/plugin dependency (V2)"
    assert "@opencode-ai/plugin" not in content, "package.json still contains deprecated @opencode-ai/plugin"


def test_plugin_exports_default_define():
    """plugins/pipeline-enforcement.ts exports default Plugin.define (V2 API)."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    assert "export default" in content, "export default not found in plugin file"
    assert "Plugin.define" in content, "Plugin.define not found in plugin file"
    assert "pipeline-enforcement" in content, "pipeline-enforcement id not found in plugin file"
    # Ensure old V1 named export is gone
    assert "export const PipelineEnforcement" not in content, "Old V1 named export PipelineEnforcement still present"


def test_plugin_has_tool_hook():
    """plugins/pipeline-enforcement.ts registers execute.before hook via ctx.tool.hook (V2)."""
    repo_root = Path(__file__).resolve().parent.parent
    plugin_file = repo_root / "plugins" / "pipeline-enforcement.ts"
    content = plugin_file.read_text()
    
    # V2: ctx.tool.hook("execute.before", ...) or "execute.before" string literal in hook call
    assert "execute.before" in content, "execute.before hook not found in plugin file"
    # Ensure old V1 hook object string is gone
    assert "\"tool.execute.before\"" not in content, "Old V1 hook object string 'tool.execute.before' still present"
