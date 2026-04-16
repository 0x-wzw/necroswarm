import { OrchestratedPlan, TaskSpec } from "@/lib/runtime/types";

export function orchestrate(task: TaskSpec, runId: string): OrchestratedPlan {
  const normalizedTask: TaskSpec = {
    ...task,
    title: task.title.trim(),
    description: task.description.trim(),
    objective: task.objective.trim(),
    acceptance_criteria: task.acceptance_criteria.map((criterion) => criterion.trim()).filter(Boolean),
    tools: {
      mcp: {
        allow: [...new Set(task.tools.mcp.allow)]
      }
    },
    skills: task.skills.map((skill) => ({
      ...skill,
      prompt: skill.prompt.trim(),
      tools_allowed: [...new Set(skill.tools_allowed)]
    }))
  };

  const complexity = normalizedTask.acceptance_criteria.length > 5 ? "large" : normalizedTask.acceptance_criteria.length > 2 ? "medium" : "small";
  const riskScore = normalizedTask.risk_level === "high" ? 0.9 : normalizedTask.risk_level === "medium" ? 0.6 : 0.3;

  return {
    run_id: runId,
    created_at: new Date().toISOString(),
    normalized_task: normalizedTask,
    derived: {
      estimated_complexity: complexity,
      risk_score: riskScore,
      objective_summary: `${normalizedTask.title}: ${normalizedTask.objective}`
    }
  };
}
