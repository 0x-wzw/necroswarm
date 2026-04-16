/**
 * System Skill — Core diagnostics and system information.
 *
 * Provides actions for:
 * - Health checks
 * - System info (uptime, memory, platform)
 * - Skill registry introspection
 * - Environment diagnostics
 */

import { defineSkill } from "../../core/define-skill.js";
import { hostname, platform, arch, uptime, freemem, totalmem } from "node:os";

export const systemSkill = defineSkill({
  manifest: {
    id: "system.diagnostics",
    name: "System Diagnostics",
    description: "Core system information, health checks, and runtime diagnostics",
    version: "0.1.0",
    tags: ["system", "diagnostics", "health"],
  },

  actions: [
    {
      name: "health",
      description: "Check system health and return status",
      async execute(_input, ctx) {
        ctx.logger.info("Health check requested");
        return {
          success: true,
          data: {
            status: "ok",
            agentId: ctx.agentId,
            runId: ctx.runId,
            timestamp: new Date().toISOString(),
          },
        };
      },
    },

    {
      name: "info",
      description: "Get system information (platform, memory, uptime)",
      async execute(_input, ctx) {
        const info = {
          hostname: hostname(),
          platform: platform(),
          arch: arch(),
          uptimeSeconds: Math.floor(uptime()),
          memory: {
            totalMb: Math.floor(totalmem() / 1024 / 1024),
            freeMb: Math.floor(freemem() / 1024 / 1024),
            usedPercent: Math.round(((totalmem() - freemem()) / totalmem()) * 100),
          },
          nodeVersion: process.version,
          agentId: ctx.agentId,
        };

        ctx.logger.info("System info collected", info);
        return { success: true, data: info };
      },
    },

    {
      name: "env",
      description: "List FRIDAY-related environment variables (redacted)",
      async execute(_input, ctx) {
        const fridayVars = Object.entries(ctx.env)
          .filter(([key]) => key.startsWith("FRIDAY_"))
          .map(([key, value]) => ({
            key,
            // Redact sensitive values
            value: key.includes("SECRET") || key.includes("KEY") || key.includes("TOKEN")
              ? "***redacted***"
              : value,
          }));

        return { success: true, data: { variables: fridayVars } };
      },
    },
  ],

  async setup(ctx) {
    ctx.logger.info("System diagnostics skill loaded");
  },
});

export default systemSkill;
