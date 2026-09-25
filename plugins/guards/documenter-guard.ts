/**
 * Documenter Guard — blocks merge if Documenter agent hasn't run
 * 
 * Checks the feature branch's commit history (branch-exclusive commits only)
 * for a commit matching the pattern "docs: reconcile". If no such commit is found,
 * throws an error instructing the user to run /document first.
 */

/**
 * Parse branch name from git merge command
 * @param command - The full command string (e.g., "git merge feature/11-08-documenter-guard")
 * @returns The branch name, or null if not a merge command
 */
function parseBranchFromMergeCommand(command: string): string | null {
  const match = command.match(/git\s+merge\s+(\S+)/)
  return match ? match[1] : null
}

/**
 * Documenter Guard — ensures Documenter has run before merge
 * 
 * @param command - The full command being executed
 * @param directory - The working directory
 * @param $ - Bun's shell API
 * @throws Error if no documenter commit found on the branch
 */
export async function documenterGuard(
  command: string,
  directory: string,
  $: any
): Promise<void> {
  // Parse branch name from git merge command
  const branch = parseBranchFromMergeCommand(command)
  
  // If not a merge command, return silently
  if (!branch) {
    return
  }
  
  // Check for documenter commit on the branch (branch-exclusive commits only)
  // The Documenter agent commits with message pattern "docs: reconcile *"
  const gitLogCommand = `git log main..${branch} --oneline --grep="docs: reconcile"`
  
  try {
    const result = await $`${gitLogCommand}`
    const output = result.stdout.toString().trim()
    
    // If no matching commits found, throw error
    if (!output) {
      throw new Error(
        `Documenter not run. Execute /document on branch ${branch} before merging.`
      )
    }
    
    // If documenter commit found, return silently
    return
  } catch (error: any) {
    // Re-throw our custom error, or throw git errors as-is
    if (error.message?.includes("Documenter not run")) {
      throw error
    }
    // If it's a git error (e.g., branch not found), let it propagate
    throw error
  }
}
