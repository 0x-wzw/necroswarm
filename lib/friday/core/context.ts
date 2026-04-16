/**
 * Skill Context Factory — Creates isolated runtime contexts for skills.
 *
 * Each skill gets its own:
 * - Scoped logger (prefixed with skill ID)
 * - Scoped key-value store
 * - Event emitter
 * - Environment access
 */

import type { SkillContext, SkillLogger, SkillStore } from "../types/index.js";
import { randomUUID } from "node:crypto";

interface ContextOptions {
  skillId: string;
  agentId?: string;
  runId?: string;
  emit: (event: string, payload: unknown) => void;
}

export function createSkillContext(opts: ContextOptions): SkillContext {
  const { skillId, emit } = opts;
  const agentId = opts.agentId ?? process.env.FRIDAY_AGENT_ID ?? "friday-default";
  const runId = opts.runId ?? process.env.FRIDAY_RUN_ID ?? randomUUID();

  return {
    runId,
    agentId,
    logger: createLogger(skillId),
    store: createMemoryStore(skillId),
    emit,
    env: Object.fromEntries(
      Object.entries(process.env).filter(([, v]) => v !== undefined) as [string, string][]
    ),
  };
}

function createLogger(prefix: string): SkillLogger {
  const fmt = (level: string, msg: string, data?: Record<string, unknown>) => {
    const entry = {
      level,
      skill: prefix,
      msg,
      ts: new Date().toISOString(),
      ...data,
    };
    const line = JSON.stringify(entry);
    if (level === "error") {
      process.stderr.write(line + "\n");
    } else {
      process.stdout.write(line + "\n");
    }
  };

  return {
    info: (msg, data) => fmt("info", msg, data),
    warn: (msg, data) => fmt("warn", msg, data),
    error: (msg, data) => fmt("error", msg, data),
    debug: (msg, data) => fmt("debug", msg, data),
  };
}

/** In-memory store scoped per skill. Swap for persistent backend later. */
const globalStore = new Map<string, unknown>();

function createMemoryStore(skillId: string): SkillStore {
  const keyPrefix = `${skillId}:`;

  return {
    async get(key: string) {
      return globalStore.get(keyPrefix + key);
    },
    async set(key: string, value: unknown) {
      globalStore.set(keyPrefix + key, value);
    },
    async delete(key: string) {
      globalStore.delete(keyPrefix + key);
    },
    async list(prefix?: string) {
      const fullPrefix = keyPrefix + (prefix ?? "");
      return Array.from(globalStore.keys())
        .filter((k) => k.startsWith(fullPrefix))
        .map((k) => k.slice(keyPrefix.length));
    },
  };
}
