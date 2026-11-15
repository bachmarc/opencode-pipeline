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
 * Validates story IDs by scanning story file names under docs/features/*/stories/*.md.
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

  // Scan story files under docs/features/*/stories/*.md for known story IDs
  // Story file names have format: XX-YY-<slug>.md (e.g., 37-03-plugin-prompt-stories-md-deletion.md)
  const docsDir = path.join(directory, "docs", "features")
  const knownStoryIds = new Set<string>()
  
  try {
    // Read all feature directories
    const featureDirs = fs.readdirSync(docsDir)
    for (const featureDir of featureDirs) {
      const storiesDir = path.join(docsDir, featureDir, "stories")
      if (!fs.existsSync(storiesDir)) {
        continue
      }
      
      // Read story files from this feature's stories directory
      const storyFiles = fs.readdirSync(storiesDir)
      for (const file of storyFiles) {
        // Extract story ID from filename (XX-YY-<slug>.md)
        // Only process .md files that match the pattern
        if (file.endsWith(".md") && !file.startsWith("_")) {
          const storyIdMatch = file.match(/^(\d{2}-\d{2})/)
          if (storyIdMatch) {
            knownStoryIds.add(storyIdMatch[1])
          }
        }
      }
    }
  } catch (error) {
    // docs/features dir may not exist yet in some contexts
    warnings.push(`Could not scan story files at ${docsDir}: ${error instanceof Error ? error.message : String(error)}`)
    return warnings
  }

  // Check each found story ID against known story IDs
  for (const storyId of foundStoryIds) {
    if (!knownStoryIds.has(storyId)) {
      warnings.push(`Unknown story ID: ${storyId} (no story file found in docs/features/*/stories/)`)
    }
  }

  return warnings
}
