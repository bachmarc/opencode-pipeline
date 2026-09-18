/**
 * SessionState — session-scoped state holder for plugin guards.
 * Tracks whether recovery has been performed in the current session.
 */
export class SessionState {
  private _recoveryDone: boolean = false

  /**
   * Mark recovery as completed for this session.
   */
  markRecoveryDone(): void {
    this._recoveryDone = true
  }

  /**
   * Check if recovery has been completed in this session.
   */
  isRecoveryDone(): boolean {
    return this._recoveryDone
  }
}
