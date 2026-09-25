import { existsSync } from "fs"
import { join } from "path"

/**
 * Session Recovery Guard — blocks tool execution if session recovery is needed.
 * 
 * Resolves the session_recovery.py script from the framework installation directory
 * using import.meta.dirname (plugin's own directory) + ../scripts/ relative path.
 * This ensures the guard works in any project, not just the dogfood repo.
 * 
 * On first tool call of a session, runs the recovery check script.
 * If recovery items exist (exit code 1), throws an error with recovery instructions.
 * If the script is not found, throws "Framework not installed" error (fail-closed).
 * 
 * Only applies to "architect" and "build" agents.
 */
export async function sessionRecoveryGuard(
  agent: string,
  directory: string,
  $: any
): Promise<void> {
  // Only architect and build agents need recovery checks
  if (agent !== "architect" && agent !== "build") {
    return
  }

  // Resolve script path relative to framework installation (plugin's directory)
  const scriptPath = join(import.meta.dirname, "..", "scripts", "session_recovery.py")
  
  // Check if recovery script exists — fail-closed if not found
  if (!existsSync(scriptPath)) {
    throw new Error(
      `Framework not installed: session_recovery.py not found at ${scriptPath}. Reinstall opencode-pipeline.`
    )
  }

  // Run recovery check
  try {
    const result = await $`python3 ${scriptPath} --check`
    // Exit code 0 = clean, no recovery needed
    return
  } catch (error: any) {
    // Exit code 1 = recovery items exist
    const exitCode = error.exitCode || error.code
    if (exitCode === 1) {
      const stderr = error.stderr?.toString() || error.message || ""
      throw new Error(
        `Session recovery required before continuing.\n\n${stderr}\n\nRun ${scriptPath} and address open items.`
      )
    }
    // Other exit codes are unexpected, re-throw
    throw error
  }
}
