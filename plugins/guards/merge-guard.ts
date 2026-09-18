import { readdirSync, readFileSync } from "fs"
import { join } from "path"

/**
 * Merge Guard: Blocks git merge commands when no QA-PASS exists for the branch.
 * 
 * Detects `git merge <branch>` pattern and checks for a corresponding QA-PASS
 * in `.pipeline/qa-state/<story-id>-<slug>.json`.
 * 
 * @param command - The full command string (e.g., "git merge feature/11-02-merge-guard")
 * @param directory - The project directory containing .pipeline/qa-state/
 * @throws Error if no QA-PASS found for the branch
 */
export function mergeGuard(command: string, directory: string): void {
  // Regex to detect git merge commands and extract branch name
  const mergePattern = /^git\s+merge\s+([^\s]+)/
  const match = command.match(mergePattern)

  if (!match) {
    // Not a merge command, allow it
    return
  }

  const branchName = match[1]

  // Extract story ID and slug from branch name (feature/<story-id>-<slug>)
  const branchPattern = /^feature\/([^-]+-[^-]+)(?:-|$)/
  const branchMatch = branchName.match(branchPattern)

  if (!branchMatch) {
    // Branch doesn't match expected pattern, allow it
    return
  }

  const storyId = branchMatch[1]
  const qaStateDir = join(directory, ".pipeline", "qa-state")
  const qaStatusFile = join(qaStateDir, `${storyId}.json`)

  try {
    // Check if QA status file exists
    const files = readdirSync(qaStateDir)
    const statusFileName = `${storyId}.json`

    if (!files.includes(statusFileName)) {
      throw new Error(
        `Merge blocked: no QA-PASS for branch ${branchName}. Run QA first.`
      )
    }

    // Read and check the QA status
    const statusContent = readFileSync(qaStatusFile, "utf-8")
    const status = JSON.parse(statusContent)

    if (status.last_verdict !== "PASS") {
      throw new Error(
        `Merge blocked: no QA-PASS for branch ${branchName}. Run QA first.`
      )
    }

    // QA-PASS found, allow merge
  } catch (error) {
    // If it's our custom error, re-throw it
    if (error instanceof Error && error.message.includes("Merge blocked")) {
      throw error
    }
    // For other errors (file not found, parse error), also block the merge
    throw new Error(
      `Merge blocked: no QA-PASS for branch ${branchName}. Run QA first.`
    )
  }
}
