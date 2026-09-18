import type { Plugin } from "@opencode-ai/plugin"
import { storyStatusGuard } from "./guards/story-status-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Run all registered guards
      for (const guard of guards) {
        await guard(input, output)
      }
    },
    "tool.execute.after": async (input: any, output: any) => {
      // Check if this was a bash tool execution
      if (input.tool === "bash") {
        const command = output.args?.command || ""
        const warning = storyStatusGuard(command, directory)
        if (warning) {
          console.warn(warning)
        }
      }
    },
  }
}
