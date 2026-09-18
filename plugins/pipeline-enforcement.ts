import type { Plugin } from "@opencode-ai/plugin"
import { documenterGuard } from "./guards/documenter-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Check for documenter guard on bash tool git merge commands
      if (input.tool === "bash" && output.args.command?.includes("git merge")) {
        await documenterGuard(output.args.command, directory, $)
      }
      
      // Run all registered guards
      for (const guard of guards) {
        await guard(input, output)
      }
    },
  }
}
