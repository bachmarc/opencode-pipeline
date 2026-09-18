/**
 * Housekeeping Log — tracks architect code edits approved as housekeeping
 * 
 * Appends entries to .pipeline/housekeeping-log.md with timestamp, file, agent, and description.
 */

import * as fs from "fs"
import * as path from "path"

const LOG_FILE = ".pipeline/housekeeping-log.md"
const LOG_HEADER = `| Timestamp | File | Agent | Description |
|---|---|---|---|`

/**
 * Append a housekeeping entry to the log
 * @param directory - The project directory
 * @param filePath - The file that was edited
 * @param agent - The agent that made the edit
 * @param description - Description of the change
 */
export function appendHousekeepingEntry(
  directory: string,
  filePath: string,
  agent: string,
  description: string
): void {
  const logPath = path.join(directory, LOG_FILE)
  const logDir = path.dirname(logPath)

  // Ensure .pipeline directory exists
  if (!fs.existsSync(logDir)) {
    fs.mkdirSync(logDir, { recursive: true })
  }

  // Create file with header if it doesn't exist
  if (!fs.existsSync(logPath)) {
    fs.writeFileSync(logPath, LOG_HEADER + "\n")
  }

  // Append entry
  const timestamp = new Date().toISOString()
  const entry = `| ${timestamp} | ${filePath} | ${agent} | ${description} |`
  fs.appendFileSync(logPath, entry + "\n")
}
