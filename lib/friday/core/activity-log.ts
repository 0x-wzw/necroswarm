/**
 * Activity Log — Immutable audit trail for all skill actions.
 *
 * Inspired by Paperclip's activity log pattern:
 * - Every mutation is recorded with actor, timestamp, and change
 * - Entries are append-only (immutable)
 * - Enables governance, debugging, and accountability
 */

export interface ActivityEntry {
  id: string;
  timestamp: Date;
  /** Who performed the action (agent ID or "system") */
  actor: string;
  /** What type of action (skill.action, heartbeat, system) */
  type: string;
  /** Which entity was affected */
  entityType?: string;
  entityId?: string;
  /** Human-readable description */
  description: string;
  /** Structured data about the change */
  metadata?: Record<string, unknown>;
  /** Run ID for tracing across heartbeats */
  runId?: string;
}

export class ActivityLog {
  private entries: ActivityEntry[] = [];
  private idCounter = 0;

  append(
    entry: Omit<ActivityEntry, "id" | "timestamp">
  ): ActivityEntry {
    const full: ActivityEntry = {
      ...entry,
      id: `act_${++this.idCounter}`,
      timestamp: new Date(),
    };
    this.entries.push(full);
    return full;
  }

  query(opts?: {
    actor?: string;
    type?: string;
    entityType?: string;
    entityId?: string;
    runId?: string;
    limit?: number;
    offset?: number;
  }): ActivityEntry[] {
    let results = this.entries;

    if (opts?.actor) results = results.filter((e) => e.actor === opts.actor);
    if (opts?.type) results = results.filter((e) => e.type === opts.type);
    if (opts?.entityType) results = results.filter((e) => e.entityType === opts.entityType);
    if (opts?.entityId) results = results.filter((e) => e.entityId === opts.entityId);
    if (opts?.runId) results = results.filter((e) => e.runId === opts.runId);

    const offset = opts?.offset ?? 0;
    const limit = opts?.limit ?? 100;

    return results.slice(offset, offset + limit);
  }

  count(): number {
    return this.entries.length;
  }

  latest(n = 10): ActivityEntry[] {
    return this.entries.slice(-n);
  }
}
