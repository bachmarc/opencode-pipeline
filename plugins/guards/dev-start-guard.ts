import * as fs from "fs"
import * as path from "path"

/**
 * Dev-Start Guard: warns when developer/qa-manager is spawned without referencing a known story.
 * 
 * Returns array of warning messages (empty if all OK).
 * This guard is ADVISORY (returns warnings), not blocking (does not throw).
 */
export function devStartGuard(
  subagentType: string,
  prompt: string,
  directory: string
): string[] {
  const warnings: string[] = []

  // Parse story IDs from prompt using regex pattern \b(\d{2}-\d{2})\b
  const storyIdRegex = /\b(\d{2}-\d{2})\b/g
  const foundStoryIds = new Set<string>()
  let match
  while ((match = storyIdRegex.exec(prompt)) !== null) {
    foundStoryIds.add(match[1])
  }

  // If no story ID found in prompt, warn
  if (foundStoryIds.size === 0) {
    warnings.push(
      `No story ID found in prompt for ${subagentType} spawn. Expected format: XX-YY (e.g., 11-01)`
    )
    return warnings
  }

  // Read STORIES.md and parse story statuses
  const storiesPath = path.join(directory, "STORIES.md")
  let storiesContent: string
  try {
    storiesContent = fs.readFileSync(storiesPath, "utf-8")
  } catch (error) {
    warnings.push(`Could not read STORIES.md at ${storiesPath}`)
    return warnings
  }

  // Parse STORIES.md table: extract story ID and status
  // Format: | story-id | title | status | traceability |
  const storyStatusMap = new Map<string, string>()
  const lines = storiesContent.split("\n")
  for (const line of lines) {
    // Skip header and separator lines
    if (line.startsWith("|") && !line.includes("---")) {
      const parts = line.split("|").map((p) => p.trim())
      if (parts.length >= 4) {
        const rawId = parts[1]
        // Row IDs carry slugs (e.g. 12-01-qa-config-contract); normalize to bare
        // XX-YY / RETRO-XX by keeping the first two dash-separated segments.
        const storyId = rawId.split("-").slice(0, 2).join("-")
        const status = parts[3]
        // Only store if storyId matches pattern XX-YY or RETRO-XX
        if (storyId && /^(\d{2}-\d{2}|RETRO-\d{2})$/.test(storyId)) {
          storyStatusMap.set(storyId, status)
        }
      }
    }
  }

  // Check each found story ID
  for (const storyId of foundStoryIds) {
    if (!storyStatusMap.has(storyId)) {
      warnings.push(`Unknown story ID: ${storyId} (not found in STORIES.md)`)
    } else {
      const status = storyStatusMap.get(storyId) || ""
      // Warn if story is already "Done"
      if (status.includes("Done")) {
        warnings.push(`Story ${storyId} is already Done (status: ${status})`)
      }
    }
  }

  return warnings
}
