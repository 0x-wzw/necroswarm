/**
 * Memory Skill — Persistent key-value memory for the agent.
 *
 * Inspired by Paperclip's para-memory-files skill and agent session persistence.
 * Provides actions for:
 * - Storing and retrieving memories (key-value pairs)
 * - Listing stored memories
 * - Session context management
 */

import { defineSkill } from "../../core/define-skill.js";

export const memorySkill = defineSkill({
  manifest: {
    id: "agent.memory",
    name: "Agent Memory",
    description: "Persistent key-value memory store for cross-session context",
    version: "0.1.0",
    tags: ["memory", "persistence", "context"],
  },

  actions: [
    {
      name: "remember",
      description: "Store a value in memory with a given key",
      inputSchema: {
        type: "object",
        properties: {
          key: { type: "string", description: "Memory key" },
          value: { description: "Value to store (any JSON-serializable value)" },
        },
        required: ["key", "value"],
      },
      async execute(input, ctx) {
        const { key, value } = input as { key: string; value: unknown };
        await ctx.store.set(key, value);
        ctx.logger.info("Memory stored", { key });
        ctx.emit("memory.stored", { key, agentId: ctx.agentId });
        return { success: true, data: { key, stored: true } };
      },
    },

    {
      name: "recall",
      description: "Retrieve a value from memory by key",
      inputSchema: {
        type: "object",
        properties: {
          key: { type: "string", description: "Memory key to recall" },
        },
        required: ["key"],
      },
      async execute(input, ctx) {
        const { key } = input as { key: string };
        const value = await ctx.store.get(key);

        if (value === undefined) {
          ctx.logger.debug("Memory miss", { key });
          return { success: true, data: { key, found: false, value: null } };
        }

        ctx.logger.debug("Memory hit", { key });
        return { success: true, data: { key, found: true, value } };
      },
    },

    {
      name: "forget",
      description: "Remove a value from memory",
      inputSchema: {
        type: "object",
        properties: {
          key: { type: "string", description: "Memory key to forget" },
        },
        required: ["key"],
      },
      async execute(input, ctx) {
        const { key } = input as { key: string };
        await ctx.store.delete(key);
        ctx.logger.info("Memory deleted", { key });
        ctx.emit("memory.deleted", { key, agentId: ctx.agentId });
        return { success: true, data: { key, deleted: true } };
      },
    },

    {
      name: "list",
      description: "List all memory keys, optionally filtered by prefix",
      inputSchema: {
        type: "object",
        properties: {
          prefix: { type: "string", description: "Optional key prefix filter" },
        },
      },
      async execute(input, ctx) {
        const { prefix } = (input as { prefix?: string }) ?? {};
        const keys = await ctx.store.list(prefix);
        return { success: true, data: { keys, count: keys.length } };
      },
    },
  ],

  async setup(ctx) {
    ctx.logger.info("Agent memory skill loaded");
  },
});

export default memorySkill;
