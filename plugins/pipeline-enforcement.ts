import type { Plugin } from "@opencode-ai/plugin"
import { SessionState } from "./helpers/session-state"
import { sessionRecoveryGuard } from "./guards/session-recovery-guard"

// Guard type: each guard is a function that can inspect and block tool calls
type Guard = (input: any, output: any) => Promise<void> | void

// Guard registry — individual guard stories will add entries here
const guards: Guard[] = []

export const PipelineEnforcement: Plugin = async ({ project, client, $, directory, worktree }) => {
  // Session-scoped state: tracks whether recovery has been performed
  const sessionState = new SessionState()

  return {
    "tool.execute.before": async (input: any, output: any) => {
      // Session recovery guard runs once per session, before other guards
      if (!sessionState.isRecoveryDone()) {
        // Extract agent name from context (fallback to "unknown" if not available)
        const agentName = (input?.context?.agent || "unknown") as string
        await sessionRecoveryGuard(agentName, directory, $)
        sessionState.markRecoveryDone()
      }

      // Run all registered guards
      for (const guard of guards) {
        await guard(input, output)
      }
    },
  }
}
