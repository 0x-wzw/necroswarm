import { BotPackage, OrchestratedPlan } from "@/lib/runtime/types";

function intersectAllowedTools(plan: OrchestratedPlan): string[] {
  const taskAllow = new Set(plan.normalized_task.tools.mcp.allow);
  const skillIntersection = plan.normalized_task.skills.reduce<Set<string> | null>((acc, skill) => {
    const current = new Set(skill.tools_allowed);
    if (!acc) {
      return current;
    }

    return new Set([...acc].filter((tool) => current.has(tool)));
  }, null);

  if (!skillIntersection) {
    return [...taskAllow];
  }

  return [...taskAllow].filter((tool) => skillIntersection.has(tool));
}

export function buildBotPackage(plan: OrchestratedPlan, model: string): BotPackage {
  const allowedTools = intersectAllowedTools(plan);

  return {
    run_id: plan.run_id,
    task_id: plan.normalized_task.task_id,
    model,
    instructions:
      "Execute the task deterministically, satisfy acceptance criteria, prefer concise outputs, and call only allowed MCP tools when needed.",
    skills: plan.normalized_task.skills,
    io_schemas: {
      input: "TaskSpec",
      output: "WorkerOutput"
    },
    rubric: [
      "Meets all acceptance criteria.",
      "Uses only allowed tools.",
      "Maintains safe and policy-compliant behavior.",
      "Produces readable, structured output."
    ],
    tests: plan.normalized_task.acceptance_criteria.map((criterion, index) => ({
      name: `criterion_${index + 1}`,
      assertion: criterion
    })),
    tools: {
      mcp_scope: {
        allow: allowedTools
      }
    }
  };
}
