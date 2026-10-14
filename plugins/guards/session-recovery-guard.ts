import { existsSync } from "fs"
import { join } from "path"
import { spawnSync } from "child_process"

/**
 * Session Recovery Guard — blocks tool execution if session recovery is needed (V2).
 * 
 * Resolves the session_recovery.py script from the framework installation directory
 * using import.meta.dirname (plugin's own directory) + ../scripts/ relative path.
 * This ensures the guard works in any project, not just the dogfood repo.
 * 
 * On first tool call of a session, runs the recovery check script using spawnSync
 * (child_process, since $ is no longer provided by V2 plugin context).
 * If recovery items exist (exit code 1), throws an error with recovery instructions.
 * If the script is not found, throws "Framework not installed" error (fail-closed).
 * 
 * Only applies to "architect" and "build" agents.
 */
export async function sessionRecoveryGuard(
  agent: string,
  directory: string
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

  // Run recovery check using spawnSync (V2: no $ context available)
  const result = spawnSync("python3", [scriptPath, "--check"], { encoding: "utf8" })
  
  if (result.status === 0) {
    // Exit code 0 = clean, no recovery needed
    return
  } else if (result.status === 1) {
    // Exit code 1 = recovery items exist
    const stderr = result.stderr || result.stdout || ""
    throw new Error(
      `Session recovery required before continuing.\n\n${stderr}\n\nRun ${scriptPath} and address open items.`
    )
  } else {
    // Other exit codes are unexpected
    throw new Error(
      `Session recovery check failed with exit code ${result.status}: ${result.stderr || result.stdout || "unknown error"}`
    )
  }
}
