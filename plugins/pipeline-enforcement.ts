import type { Plugin } from "@opencode-ai/plugin"
import { mergeGuard } from "./guards/merge-guard"
import { devStartGuard } from "./guards/dev-start-guard"
import { architectCodeGuard } from "./guards/architect-code-guard"
import { storyStatusGuard } from "./guards/story-status-guard"
import { SessionState } from "./helpers/session-state"
import { sessionRecoveryGuard } from "./guards/session-recovery-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  // Capture agent from context (will be available in input during tool execution)
  let currentAgent = "unknown"

  // Session-scoped state: tracks whether recovery has been performed
  const sessionState = new SessionState()

  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Extract agent from input metadata if available
      if (input.metadata?.agent) {
        currentAgent = input.metadata.agent
      }
      const agentName = input?.context?.agent || currentAgent || "unknown"

      // Session recovery guard runs once per session, before other guards
      if (!sessionState.isRecoveryDone()) {
        await sessionRecoveryGuard(agentName, directory, $)
        sessionState.markRecoveryDone()
      }

      // Check merge guard for bash tool calls
      if (input.tool === "bash" && output.args?.command) {
        const command = output.args.command
        if (command.includes("git merge")) {
          mergeGuard(command, directory)
        }
      }

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

      // Check architect code guard for edit and write tools
      if ((input.tool === "edit" || input.tool === "write") && output.args?.filePath) {
        const result = architectCodeGuard(
          agentName,
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
