import { resolveAuthToken } from "@/lib/mcp/auth";
import { DeployStepResult } from "@/lib/deployment/types";

function makeStep(step: string, status: DeployStepResult["status"], output: string, start: number): DeployStepResult {
  return { step, status, output, duration_ms: Date.now() - start };
}

export async function gitPull(repo: string, branch: string): Promise<DeployStepResult> {
  const start = Date.now();
  // Stubbed: in production would run `git pull origin <branch>` via SSH or GitHub API
  return makeStep(
    "deploy.git_pull",
    "ok",
    `Pulled branch '${branch}' from '${repo}' (stubbed)`,
    start
  );
}

export async function buildDocker(repo: string, tag: string): Promise<DeployStepResult> {
  const start = Date.now();
  // Stubbed: in production would run `docker build -t <tag> .`
  return makeStep(
    "deploy.build_docker",
    "ok",
    `Built Docker image '${tag}' for '${repo}' (stubbed)`,
    start
  );
}

export async function pushToRegistry(tag: string, registryEnvRef: string): Promise<DeployStepResult> {
  const start = Date.now();
  const registryUrl = resolveAuthToken(registryEnvRef) ?? "<registry-not-configured>";
  // Stubbed: in production would run `docker push <registryUrl>/<tag>`
  return makeStep(
    "deploy.push_registry",
    "ok",
    `Pushed '${tag}' to registry '${registryUrl}' (stubbed)`,
    start
  );
}

export async function deployContainer(hostEnvRef: string, tag: string): Promise<DeployStepResult> {
  const start = Date.now();
  const host = resolveAuthToken(hostEnvRef) ?? "<host-not-configured>";
  // Stubbed: in production would SSH to host and run deploy.sh <tag>
  return makeStep(
    "deploy.deploy_container",
    "ok",
    `Deployed '${tag}' to host '${host}' via deploy.sh (stubbed)`,
    start
  );
}

export async function runHealthCheck(hostEnvRef: string, path = "/api/health"): Promise<DeployStepResult> {
  const start = Date.now();
  const host = resolveAuthToken(hostEnvRef) ?? "<host-not-configured>";
  // Stubbed: in production would GET http://<host><path> and assert 200
  return makeStep(
    "deploy.health_check",
    "ok",
    `Health check passed at 'http://${host}${path}' (stubbed)`,
    start
  );
}

export async function rollback(hostEnvRef: string, previousTag: string): Promise<DeployStepResult> {
  const start = Date.now();
  const host = resolveAuthToken(hostEnvRef) ?? "<host-not-configured>";
  // Stubbed: in production would SSH to host and redeploy the previous image tag
  return makeStep(
    "deploy.rollback",
    "ok",
    `Rolled back to '${previousTag}' on host '${host}' (stubbed)`,
    start
  );
}

export const DEPLOY_TOOL_NAMES = [
  "deploy.git_pull",
  "deploy.build_docker",
  "deploy.push_registry",
  "deploy.deploy_container",
  "deploy.health_check",
  "deploy.rollback"
] as const;
