import type { Plugin } from "@opencode-ai/plugin"
import { devStartGuard } from "./guards/dev-start-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Check for dev-start guard: if spawning developer or qa-manager without story
      if (input.tool === "task") {
        const subagentType = output.args?.subagent_type
        const prompt = output.args?.prompt || ""
        
        if (subagentType === "developer" || subagentType === "qa-manager") {
          const warnings = devStartGuard(subagentType, prompt, directory)
          for (const warning of warnings) {
            console.warn(`[Dev-Start Guard] ${warning}`)
          }
        }
      }

      // Run all registered guards
      for (const guard of guards) {
        await guard(input, output)
      }
    },
  }
}
