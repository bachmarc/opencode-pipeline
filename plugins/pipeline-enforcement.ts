import type { Plugin } from "@opencode-ai/plugin"

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
  }
}
