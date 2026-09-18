import type { Plugin } from "@opencode-ai/plugin"
import { architectCodeGuard } from "./guards/architect-code-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  // Capture agent from context (will be available in input during tool execution)
  let currentAgent = "unknown"

  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Extract agent from input metadata if available
      if (input.metadata?.agent) {
        currentAgent = input.metadata.agent
      }

      // Check architect code guard for edit and write tools
      if ((input.tool === "edit" || input.tool === "write") && output.args?.filePath) {
        const result = architectCodeGuard(
          currentAgent,
          input.tool,
          output.args.filePath,
          directory
        )

        if (result.action === "block") {
          throw new Error(result.reason)
        }
      }

      // Run all registered guards
      for (const guard of guards) {
        await guard(input, output)
      }
    },
  }
}
