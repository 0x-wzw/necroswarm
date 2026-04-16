import { callLLM } from "@/lib/runtime/llm";
import { BotPackage, TaskSpec, WorkerOutput } from "@/lib/runtime/types";
import { routeToolCall } from "@/lib/runtime/toolRouter";

interface WorkerInput {
  taskSpec: TaskSpec;
  botPackage: BotPackage;
  artifactsDir: string;
  maxOutputTokens: number;
}

const COST_PER_1K_OUTPUT: Record<string, number> = {
  "openai:gpt-4o-mini": 0.0006,
  "openai:gpt-4o": 0.015,
  "openai:gpt-5": 0.03
};

export async function runWorker(input: WorkerInput): Promise<WorkerOutput> {
  const toolCalls: WorkerOutput["tool_calls"] = [];
  const firstSkill = input.taskSpec.skills[0];

  if (firstSkill?.tools_allowed.length) {
    const candidateTool = firstSkill.tools_allowed[0];
    const serverId = candidateTool.startsWith("necroswarm.") ? "necroswarm" : "remote_default";
    try {
      const mcpResponse = await routeToolCall(
        {
          skill_id: firstSkill.skill_id,
          server_id: serverId,
          tool: candidateTool,
          args: { query: input.taskSpec.objective }
        },
        {
          artifactsDir: input.artifactsDir,
          taskSpec: input.taskSpec,
          botPackage: input.botPackage
        }
      );

      toolCalls.push({
        tool: candidateTool,
        server_id: serverId,
        result: mcpResponse.data,
        ok: mcpResponse.ok
      });
    } catch (error) {
      toolCalls.push({
        tool: candidateTool,
        server_id: serverId,
        result: { error: (error as Error).message },
        ok: false
      });
    }
  }

  const llmResponse = await callLLM({
    model: input.botPackage.model,
    system: `${input.botPackage.instructions}\nAllowed tools: ${input.botPackage.tools.mcp_scope.allow.join(",")}`,
    prompt: JSON.stringify(
      {
        task_id: input.taskSpec.task_id,
        title: input.taskSpec.title,
        objective: input.taskSpec.objective,
        acceptance_criteria: input.taskSpec.acceptance_criteria,
        tool_results: toolCalls.map((call) => ({ tool: call.tool, ok: call.ok }))
      },
      null,
      2
    ),
    maxOutputTokens: input.maxOutputTokens
  });

  const estimated_cost_usd = Number(((llmResponse.usage.output_tokens / 1000) * (COST_PER_1K_OUTPUT[input.botPackage.model] ?? 0.03)).toFixed(6));

  return {
    status: "completed",
    model_used: input.botPackage.model,
    content: llmResponse.content,
    tool_calls: toolCalls,
    estimated_cost_usd
  };
}
