import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

import { executeMcpTool } from "@/lib/mcp/client";
import { BotPackage, TaskSpec } from "@/lib/runtime/types";

export interface ToolCall {
  skill_id: string;
  tool: string;
  server_id: string;
  args: Record<string, unknown>;
}

export interface ToolRouterContext {
  artifactsDir: string;
  taskSpec: TaskSpec;
  botPackage: BotPackage;
}

function intersection(a: string[], b: string[]): string[] {
  const right = new Set(b);
  return [...new Set(a)].filter((item) => right.has(item));
}

function allowedForSkill(skillId: string, taskSpec: TaskSpec, botPackage: BotPackage): string[] {
  const taskAllow = taskSpec.tools.mcp.allow;
  const packageAllow = botPackage.tools.mcp_scope.allow;
  const skill = taskSpec.skills.find((candidate) => candidate.skill_id === skillId);
  if (!skill) {
    return [];
  }

  return intersection(intersection(taskAllow, packageAllow), skill.tools_allowed);
}

async function writeTrace(artifactsDir: string, trace: Record<string, unknown>) {
  await mkdir(artifactsDir, { recursive: true });
  const tracePath = path.join(artifactsDir, "tool_traces.jsonl");
  await appendFile(tracePath, `${JSON.stringify(trace)}\n`, "utf8");
}

export async function routeToolCall(call: ToolCall, context: ToolRouterContext) {
  const allowlist = allowedForSkill(call.skill_id, context.taskSpec, context.botPackage);
  const allowed = allowlist.includes(call.tool);

  if (!allowed) {
    const deniedTrace = {
      ts: new Date().toISOString(),
      status: "denied",
      tool: call.tool,
      skill_id: call.skill_id,
      server_id: call.server_id,
      reason: "Tool not in intersection allowlist"
    };
    await writeTrace(context.artifactsDir, deniedTrace);
    throw new Error(`Tool ${call.tool} is not allowed for skill ${call.skill_id}.`);
  }

  const result = await executeMcpTool({
    server_id: call.server_id,
    tool: call.tool,
    args: call.args
  });

  await writeTrace(context.artifactsDir, {
    ts: new Date().toISOString(),
    status: result.ok ? "ok" : "error",
    skill_id: call.skill_id,
    server_id: call.server_id,
    tool: call.tool,
    args_shape: Object.keys(call.args),
    transport: result.transport
  });

  return result;
}
