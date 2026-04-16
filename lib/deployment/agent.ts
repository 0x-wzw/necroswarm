import { appendFile, mkdir } from "node:fs/promises";
import path from "node:path";

import { callLLM } from "@/lib/runtime/llm";
import { DeploymentSpec, DeploymentResult, DeployStepResult } from "@/lib/deployment/types";
import {
  gitPull,
  buildDocker,
  pushToRegistry,
  deployContainer,
  runHealthCheck,
  rollback
} from "@/lib/deployment/tools";

const DEPLOY_MODEL = "openai:gpt-4o-mini";

async function writeStepTrace(artifactsDir: string, step: DeployStepResult): Promise<void> {
  await mkdir(artifactsDir, { recursive: true });
  const tracePath = path.join(artifactsDir, "deploy_steps.jsonl");
  await appendFile(tracePath, `${JSON.stringify({ ...step, ts: new Date().toISOString() })}\n`, "utf8");
}

export async function runDeploymentAgent(
  spec: DeploymentSpec,
  runId: string,
  artifactsDir: string
): Promise<DeploymentResult> {
  const triggeredAt = new Date().toISOString();
  const imageTag = `${spec.repo.replace("/", "-")}:${spec.branch}-${spec.deploy_id}`;
  const steps: DeployStepResult[] = [];

  // GPT planning step: generate deployment summary/checklist
  await callLLM({
    model: DEPLOY_MODEL,
    system:
      "You are a DevOps deployment agent. Given a deployment spec, produce a concise ordered checklist of deployment steps and any risks to watch for. Be brief.",
    prompt: JSON.stringify({ repo: spec.repo, branch: spec.branch, env: spec.target.env, image_tag: imageTag }),
    maxOutputTokens: 256
  });

  // Sequential deployment pipeline
  let failed = false;

  const pipeline: Array<() => Promise<DeployStepResult>> = [
    () => gitPull(spec.repo, spec.branch),
    () => buildDocker(spec.repo, imageTag),
    () => pushToRegistry(imageTag, spec.target.registry_env_ref),
    () => deployContainer(spec.target.host_env_ref, imageTag),
    () => runHealthCheck(spec.target.host_env_ref)
  ];

  for (const action of pipeline) {
    if (failed) {
      break;
    }
    const result = await action();
    steps.push(result);
    await writeStepTrace(artifactsDir, result);
    if (result.status === "failed") {
      failed = true;
    }
  }

  let overall: DeploymentResult["overall"] = failed ? "failure" : "success";

  if (failed) {
    const rbResult = await rollback(spec.target.host_env_ref, `${imageTag}-prev`);
    steps.push(rbResult);
    await writeStepTrace(artifactsDir, rbResult);
    if (rbResult.status === "ok") {
      overall = "rolled_back";
    }
  }

  return {
    deploy_id: spec.deploy_id,
    run_id: runId,
    overall,
    steps,
    triggered_at: triggeredAt,
    completed_at: new Date().toISOString()
  };
}
