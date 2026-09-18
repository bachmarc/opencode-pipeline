import * as fs from "fs"
import * as path from "path"

/**
 * Story Status Guard
 * 
 * Checks if STORIES.md was updated after a git merge.
 * Returns a warning message if the story status is not marked as "Done",
 * or null if the check passes.
 */
export function storyStatusGuard(command: string, directory: string): string | null {
  // Parse branch name from git merge command
  // Pattern: git merge <branch-name>
  const mergeMatch = command.match(/git\s+merge\s+(\S+)/)
  if (!mergeMatch) {
    return null
  }

  const branchName = mergeMatch[1]

  // Extract story ID from branch name
  // Pattern: feature/<story-id>-<slug>
  // Example: feature/11-05-story-status-guard -> 11-05
  const storyIdMatch = branchName.match(/feature\/([^-]+-[^-]+)/)
  if (!storyIdMatch) {
    return null
  }

  const storyId = storyIdMatch[1]

  // Read STORIES.md
  const storiesPath = path.join(directory, "STORIES.md")
  let content: string
  try {
    content = fs.readFileSync(storiesPath, "utf-8")
  } catch {
    // If STORIES.md doesn't exist or can't be read, skip the check
    return null
  }

  // Find the line containing the story ID
  const lines = content.split("\n")
  const storyLine = lines.find((line) => line.includes(storyId))

  if (!storyLine) {
    // Story not found in STORIES.md, skip the check
    return null
  }

  // Check if the line contains "Done" (case-insensitive)
  if (!/Done/i.test(storyLine)) {
    return `STORIES.md not updated for ${storyId} after merge. Please update status to Done.`
  }

  return null
}
