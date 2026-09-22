import * as fs from "fs"
import * as path from "path"

/**
 * Dev-Start Guard: warns when developer/qa-manager is spawned without referencing a known story.
 * 
 * Explicit marker convention: prompts should start with [story: XX-YY] to identify the target story.
 * This avoids false positives from other XX-YY patterns in the text (e.g., "watermark synced_through: 14-01").
 * 
 * If explicit marker is found, only that story is checked.
 * If no marker is found, falls back to regex pattern matching (backward compatible) with a warning.
 * 
 * Returns array of warning messages (empty if all OK).
 * This guard is ADVISORY (returns warnings), not blocking (does not throw).
 */

/**
 * Parse explicit [story: XX-YY] marker from prompt.
 * 
 * Looks for pattern like:
 *   [story: 15-02]
 *   [story:15-02]
 *   [ story: 15-02 ]
 * 
 * Case-insensitive, allows whitespace variations.
 * 
 * @param prompt The prompt text to search
 * @returns The story ID (e.g., "15-02") if found, null otherwise
 */
function parseExplicitStoryId(prompt: string): string | null {
  // Match [story: XX-YY] with optional whitespace, case-insensitive
  const markerRegex = /\[\s*story\s*:\s*(\d{2}-\d{2})\s*\]/i
  const match = markerRegex.exec(prompt)
  return match ? match[1] : null
}

export function devStartGuard(
  subagentType: string,
  prompt: string,
  directory: string
): string[] {
  const warnings: string[] = []

  // Try to parse explicit [story: XX-YY] marker first
  let explicitStoryId = parseExplicitStoryId(prompt)
  let foundStoryIds = new Set<string>()

  if (explicitStoryId) {
    // Explicit marker found — only check this story
    foundStoryIds.add(explicitStoryId)
  } else {
    // No explicit marker — fall back to regex pattern matching
    warnings.push(
      `No [story: XX-YY] marker found in prompt. Using fallback pattern matching.`
    )
    
    // Parse story IDs from prompt using regex pattern \b(\d{2}-\d{2})\b
    const storyIdRegex = /\b(\d{2}-\d{2})\b/g
    let match
    while ((match = storyIdRegex.exec(prompt)) !== null) {
      foundStoryIds.add(match[1])
    }
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
