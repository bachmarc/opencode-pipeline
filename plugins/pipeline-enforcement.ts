import { Plugin } from "@opencode/plugin"
import { mergeGuard } from "./guards/merge-guard"
import { devStartGuard } from "./guards/dev-start-guard"
import { architectCodeGuard } from "./guards/architect-code-guard"
import { storyStatusGuard } from "./guards/story-status-guard"
import { SessionState } from "./helpers/session-state"
import { sessionRecoveryGuard } from "./guards/session-recovery-guard"
import { documenterGuard } from "./guards/documenter-guard"

/**
 * Pipeline Enforcement Plugin — V2 entrypoint (OpenCode V2 plugin API).
 * 
 * Registers tool execution guards that enforce development workflow constraints:
 * - Merge guard: ensures merge commits to main follow convention
 * - Documenter guard: requires /document execution before merge
 * - Dev-start guard: prevents spawning developer/qa-manager without story context
 * - Architect-code guard: architect can only edit design/planning files, not implementation
 * - Session-recovery guard: runs on first tool call to recover session state
 * - Story-status guard: on bash tool completion, checks STORIES.md alignment
 * 
 * Hooks are registered via ctx.tool.hook() calls inside setup(), not returned as object.
 * Directory context is accessed via ctx.location.directory (replaces old directory parameter).
 * Session state is session-scoped (not shared across tool calls globally).
 */

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export default Plugin.define({
  id: "pipeline-enforcement",
  async setup(ctx) {
    // Capture agent from context (will be available in input during tool execution)
    let currentAgent = "unknown"

    // Session-scoped state: tracks whether recovery has been performed
    const sessionState = new SessionState()

    // V2: Register execute.before hook via ctx.tool.hook()
    await ctx.tool.hook("execute.before", async (event: any) => {
      // Extract agent from input metadata if available
      if (event.input?.metadata?.agent) {
        currentAgent = event.input.metadata.agent
      }
      const agentName = event.input?.context?.agent || currentAgent || "unknown"
      const directory = ctx.location.directory

      // Session recovery guard runs once per session, before other guards
      if (!sessionState.isRecoveryDone()) {
        await sessionRecoveryGuard(agentName, directory)
        sessionState.markRecoveryDone()
      }

      // Check merge guard and documenter guard for bash tool git merge commands
      if (event.tool === "bash" && event.input?.command) {
        const command = event.input.command
        if (command.includes("git merge")) {
          mergeGuard(command, directory)
          await documenterGuard(command, directory)
        }
      }

      // Check for dev-start guard: if spawning developer or qa-manager without story
      if (event.tool === "task") {
        const subagentType = event.input?.subagent_type
        const prompt = event.input?.prompt || ""
        
        if (subagentType === "developer" || subagentType === "qa-manager") {
          const warnings = devStartGuard(subagentType, prompt, directory)
          for (const warning of warnings) {
            console.warn(`[Dev-Start Guard] ${warning}`)
          }
        }
      }

      // Check architect code guard for edit and write tools
      if ((event.tool === "edit" || event.tool === "write") && event.input?.filePath) {
        const result = architectCodeGuard(
          agentName,
          event.tool,
          event.input.filePath,
          directory
        )

        if (result.action === "block") {
          throw new Error(result.reason)
        }
      }

      // Run all registered guards
      for (const guard of guards) {
        await guard(event.input, event.input)
      }
    })

    // V2: Register execute.after hook via ctx.tool.hook()
    await ctx.tool.hook("execute.after", async (event: any) => {
      const directory = ctx.location.directory
      
      // Check if this was a bash tool execution
      if (event.tool === "bash") {
        const command = event.input?.command || ""
        const warning = storyStatusGuard(command, directory)
        if (warning) {
          console.warn(warning)
        }
      }
    })
  },
})
