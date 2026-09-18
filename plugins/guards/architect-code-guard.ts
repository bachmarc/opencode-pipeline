/**
 * Architect Code Guard — blocks architect from editing code files
 * 
 * Prevents the architect agent from silently modifying code files.
 * Returns "block" for architect + code file, "allow" otherwise.
 */

// Code file patterns that require pipeline review
const CODE_PATTERNS = [".py", ".ts", ".js", ".sh"]
const PATH_PATTERNS = ["src/", "tests/", "plugins/guards/"]

export interface GuardResult {
  action: "allow" | "block"
  reason: string
}

/**
 * Check if architect is trying to edit code files
 * @param agent - The agent name (e.g., "architect", "developer", "build")
 * @param tool - The tool name (e.g., "edit", "write")
 * @param filePath - The file path being edited
 * @param directory - The project directory (for context)
 * @returns GuardResult with action and reason
 */
export function architectCodeGuard(
  agent: string,
  tool: string,
  filePath: string,
  directory: string
): GuardResult {
  // Allow non-architect agents (including "build" which is opencode's default)
  if (agent !== "architect" && agent !== "build") {
    return {
      action: "allow",
      reason: "non-architect agent",
    }
  }

  // Check if file matches code patterns
  const isCodeFile =
    CODE_PATTERNS.some((pattern) => filePath.endsWith(pattern)) ||
    PATH_PATTERNS.some((pattern) => filePath.includes(pattern))

  if (!isCodeFile) {
    return {
      action: "allow",
      reason: "non-code file",
    }
  }

  // Block architect from editing code files
  return {
    action: "block",
    reason: `Architect code edit blocked: ${filePath}. Choose:
1. Housekeeping fix — will be logged in .pipeline/housekeeping-log.md
2. Full pipeline — create a story and spawn a developer
This edit was blocked by the pipeline-enforcement plugin.`,
  }
}
