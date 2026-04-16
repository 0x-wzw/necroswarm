export type DeployEnv = "staging" | "production";

export interface DeployTarget {
  env: DeployEnv;
  host_env_ref: string;
  registry_env_ref: string;
}

export interface DeploymentSpec {
  deploy_id: string;
  repo: string;
  branch: string;
  target: DeployTarget;
  require_approval: boolean;
}

export type DeployStepStatus = "ok" | "failed" | "skipped";

export interface DeployStepResult {
  step: string;
  status: DeployStepStatus;
  output: string;
  duration_ms: number;
}

export type DeploymentOverall = "success" | "failure" | "rolled_back";

export interface DeploymentResult {
  deploy_id: string;
  run_id: string;
  overall: DeploymentOverall;
  steps: DeployStepResult[];
  triggered_at: string;
  completed_at: string;
}
