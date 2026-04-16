import { OrchestratedPlan, PreflightReport } from "@/lib/runtime/types";

const HARD_BUDGET_CAP_USD = 5;

const MODEL_PRICING = [
  { model: "openai:gpt-4o-mini", inputPer1M: 0.15, outputPer1M: 0.6 },
  { model: "openai:gpt-4o", inputPer1M: 5, outputPer1M: 15 },
  { model: "openai:gpt-5", inputPer1M: 10, outputPer1M: 30 }
];

function estimateTokens(plan: OrchestratedPlan) {
  const inputBase = Math.ceil(
    (plan.normalized_task.description.length + plan.normalized_task.objective.length + JSON.stringify(plan.normalized_task.skills).length) / 3.5
  );
  const outputBase = Math.max(256, Math.ceil(plan.normalized_task.acceptance_criteria.length * 180));

  return {
    input_tokens: Math.min(plan.normalized_task.budget.max_input_tokens, inputBase),
    output_tokens: Math.min(plan.normalized_task.budget.max_output_tokens, outputBase)
  };
}

export function runBudgetGate(plan: OrchestratedPlan): PreflightReport {
  const estimate = estimateTokens(plan);
  const total = estimate.input_tokens + estimate.output_tokens;

  const costEstimates = MODEL_PRICING.map((price) => {
    const input_cost_usd = Number(((estimate.input_tokens / 1_000_000) * price.inputPer1M).toFixed(6));
    const output_cost_usd = Number(((estimate.output_tokens / 1_000_000) * price.outputPer1M).toFixed(6));
    const total_cost_usd = Number((input_cost_usd + output_cost_usd).toFixed(6));

    return {
      model: price.model,
      input_cost_usd,
      output_cost_usd,
      total_cost_usd
    };
  });

  const baseline = costEstimates[1] ?? costEstimates[0];
  const p90 = Number((baseline.total_cost_usd * 1.3).toFixed(6));
  const p95 = Number((baseline.total_cost_usd * 1.6).toFixed(6));
  const budgetLimit = Math.min(plan.normalized_task.budget.max_usd, HARD_BUDGET_CAP_USD);
  const approve = p95 <= budgetLimit && total <= plan.normalized_task.budget.max_input_tokens + plan.normalized_task.budget.max_output_tokens;

  return {
    run_id: plan.run_id,
    token_estimate: {
      input_tokens: estimate.input_tokens,
      output_tokens: estimate.output_tokens,
      total_tokens: total
    },
    cost_estimates: costEstimates,
    p90_cost_usd: p90,
    p95_cost_usd: p95,
    approve,
    reason: approve ? "Budget gate approved." : `Projected p95 cost ${p95} exceeds budget ${budgetLimit}.`,
    recommended_caps: {
      max_input_tokens: Math.min(plan.normalized_task.budget.max_input_tokens, Math.ceil(estimate.input_tokens * 1.2)),
      max_output_tokens: Math.min(plan.normalized_task.budget.max_output_tokens, Math.ceil(estimate.output_tokens * 1.2)),
      max_usd: budgetLimit
    },
    chosen_model: "openai:gpt-4o-mini"
  };
}
