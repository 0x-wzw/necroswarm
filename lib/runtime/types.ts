export type RiskLevel = "low" | "medium" | "high";

export interface TaskSpec {
  task_id: string;
  title: string;
  description: string;
  objective: string;
  context?: string;
  acceptance_criteria: string[];
  risk_level: RiskLevel;
  budget: {
    max_usd: number;
    max_input_tokens: number;
    max_output_tokens: number;
  };
  tools: {
    mcp: {
      allow: string[];
    };
  };
  skills: Array<{
    skill_id: string;
    prompt: string;
    tools_allowed: string[];
  }>;
  metadata?: Record<string, string | number | boolean | null>;
}

export interface OrchestratedPlan {
  run_id: string;
  created_at: string;
  normalized_task: TaskSpec;
  derived: {
    estimated_complexity: "small" | "medium" | "large";
    risk_score: number;
    objective_summary: string;
  };
}

export interface ModelPrice {
  model: string;
  inputPer1M: number;
  outputPer1M: number;
}

export interface PreflightReport {
  run_id: string;
  token_estimate: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  cost_estimates: Array<{
    model: string;
    input_cost_usd: number;
    output_cost_usd: number;
    total_cost_usd: number;
  }>;
  p90_cost_usd: number;
  p95_cost_usd: number;
  approve: boolean;
  reason: string;
  recommended_caps: {
    max_input_tokens: number;
    max_output_tokens: number;
    max_usd: number;
  };
  chosen_model: string;
}

export interface BotPackage {
  run_id: string;
  task_id: string;
  model: string;
  instructions: string;
  skills: TaskSpec["skills"];
  io_schemas: {
    input: string;
    output: string;
  };
  rubric: string[];
  tests: Array<{ name: string; assertion: string }>;
  tools: {
    mcp_scope: {
      allow: string[];
    };
  };
}

export interface WorkerOutput {
  status: "completed" | "failed";
  model_used: string;
  content: string;
  tool_calls: Array<{
    tool: string;
    server_id?: string;
    result: unknown;
    ok: boolean;
  }>;
  estimated_cost_usd: number;
}

export interface AuditReport {
  audit_type: "spec" | "quality" | "risk" | "budget";
  status: "pass" | "fail" | "warn";
  score: number;
  findings: string[];
  recommendations: string[];
  metadata?: Record<string, unknown>;
}

export interface FinalReleaseArtifact {
  run_id: string;
  status: "pass" | "fail";
  next_action: "release" | "revise" | "manual_review";
  model_used: string;
  estimated_cost_usd: number;
  audit_summary: {
    pass: number;
    warn: number;
    fail: number;
  };
}
