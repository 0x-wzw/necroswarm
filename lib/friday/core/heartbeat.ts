/**
 * Heartbeat Engine — Episodic execution model for agent work cycles.
 *
 * Directly inspired by Paperclip's heartbeat pattern:
 * - Agents execute in discrete "heartbeats" rather than running continuously
 * - Each heartbeat has a wake reason (task assignment, timer, mention, etc.)
 * - Context is loaded at the start and status is reported at the end
 * - Prevents runaway costs and enables audit trails
 */

import type { SkillRegistry } from "./registry.js";
import { randomUUID } from "node:crypto";

export type WakeReason = "timer" | "task_assigned" | "mention" | "manual" | "event";

export interface HeartbeatContext {
  runId: string;
  agentId: string;
  wakeReason: WakeReason;
  /** ID of the task that triggered this heartbeat (if applicable) */
  taskId?: string;
  /** Additional context passed by the trigger */
  payload?: unknown;
  timestamp: Date;
}

export interface HeartbeatResult {
  runId: string;
  status: "completed" | "blocked" | "error";
  summary: string;
  /** Actions taken during this heartbeat */
  actionsExecuted: Array<{ skill: string; action: string; success: boolean }>;
  durationMs: number;
}

export interface HeartbeatEngineConfig {
  /** Interval in ms for timer-based heartbeats (0 = disabled) */
  intervalMs: number;
  /** Maximum heartbeat duration before timeout */
  timeoutMs: number;
  agentId: string;
}

export class HeartbeatEngine {
  private registry: SkillRegistry;
  private config: HeartbeatEngineConfig;
  private timer: ReturnType<typeof setInterval> | null = null;
  private running = false;

  constructor(registry: SkillRegistry, config: HeartbeatEngineConfig) {
    this.registry = registry;
    this.config = config;
  }

  /** Start timer-based heartbeats */
  start(): void {
    if (this.config.intervalMs <= 0) return;

    this.timer = setInterval(() => {
      this.trigger("timer").catch(() => {});
    }, this.config.intervalMs);
  }

  stop(): void {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }

  /** Trigger a single heartbeat */
  async trigger(
    reason: WakeReason,
    opts?: { taskId?: string; payload?: unknown }
  ): Promise<HeartbeatResult> {
    if (this.running) {
      return {
        runId: "",
        status: "blocked",
        summary: "Another heartbeat is already running",
        actionsExecuted: [],
        durationMs: 0,
      };
    }

    this.running = true;
    const startTime = Date.now();
    const runId = randomUUID();

    const ctx: HeartbeatContext = {
      runId,
      agentId: this.config.agentId,
      wakeReason: reason,
      taskId: opts?.taskId,
      payload: opts?.payload,
      timestamp: new Date(),
    };

    const actionsExecuted: HeartbeatResult["actionsExecuted"] = [];

    try {
      // Emit heartbeat.start event so skills can react
      await this.registry.emit("heartbeat.start", ctx);

      // Emit heartbeat.complete
      await this.registry.emit("heartbeat.complete", {
        ...ctx,
        actionsExecuted,
      });

      return {
        runId,
        status: "completed",
        summary: `Heartbeat ${runId} completed (${reason})`,
        actionsExecuted,
        durationMs: Date.now() - startTime,
      };
    } catch (err) {
      return {
        runId,
        status: "error",
        summary: err instanceof Error ? err.message : String(err),
        actionsExecuted,
        durationMs: Date.now() - startTime,
      };
    } finally {
      this.running = false;
    }
  }
}
