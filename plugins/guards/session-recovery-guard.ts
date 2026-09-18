import { existsSync } from "fs"

/**
 * Session Recovery Guard — blocks tool execution if session recovery is needed.
 * 
 * On first tool call of a session, runs `scripts/session_recovery.py --check`.
 * If recovery items exist (exit code 1), throws an error with recovery instructions.
 * 
 * Only applies to "architect" and "build" agents. Safe for non-pipeline projects.
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

  // Check if recovery script exists (safe for non-pipeline projects)
  const scriptPath = `${directory}/scripts/session_recovery.py`
  if (!existsSync(scriptPath)) {
    return
  }

  // Run recovery check
  try {
    const result = await $`python3 scripts/session_recovery.py --check`
    // Exit code 0 = clean, no recovery needed
    return
  } catch (error: any) {
    // Exit code 1 = recovery items exist
    const exitCode = error.exitCode || error.code
    if (exitCode === 1) {
      const stderr = error.stderr?.toString() || error.message || ""
      throw new Error(
        `Session recovery required before continuing.\n\n${stderr}\n\nRun scripts/session_recovery.py and address open items.`
      )
    }
    // Other exit codes are unexpected, re-throw
    throw error
  }
}
