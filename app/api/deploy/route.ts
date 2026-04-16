import { randomUUID } from "node:crypto";
import path from "node:path";

import { ensureRunArtifactDir, writeArtifact } from "@/lib/runtime/artifacts";
import { assertValidSchema } from "@/lib/runtime/validator";
import { runDeploymentAgent } from "@/lib/deployment/agent";
import { checkRateLimit, recordDeploy } from "@/lib/deployment/rateLimiter";
import { DeploymentSpec, DeploymentResult } from "@/lib/deployment/types";

const APPROVAL_TOKEN_ENV = "DEPLOY_APPROVAL_TOKEN";

function getApprovalToken(): string | undefined {
  return process.env[APPROVAL_TOKEN_ENV];
}

export async function POST(request: Request): Promise<Response> {
  try {
    const body: unknown = await request.json();
    assertValidSchema<DeploymentSpec>("deploySpec", body);

    const spec = body as DeploymentSpec;

    // Rate limit check
    const rateCheck = checkRateLimit(spec.target.env);
    if (!rateCheck.allowed) {
      return Response.json(
        { status: "error", error: rateCheck.reason },
        { status: 429 }
      );
    }

    // Approval check for production or when explicitly required
    if (spec.require_approval || spec.target.env === "production") {
      const expectedToken = getApprovalToken();
      const providedToken = request.headers.get("x-deploy-approval");
      if (!expectedToken || providedToken !== expectedToken) {
        return Response.json(
          { status: "error", error: "Missing or invalid X-Deploy-Approval header." },
          { status: 403 }
        );
      }
    }

    const runId = randomUUID();
    const artifactsDir = await ensureRunArtifactDir(runId);

    recordDeploy(spec.target.env);

    const result = await runDeploymentAgent(spec, runId, artifactsDir);
    assertValidSchema<DeploymentResult>("deployResult", result);

    const resultPath = await writeArtifact(artifactsDir, "deployment_result.json", result);

    return Response.json({
      deploy_id: result.deploy_id,
      run_id: runId,
      status: result.overall,
      steps_ref: path.relative(process.cwd(), path.join(artifactsDir, "deploy_steps.jsonl")),
      result_ref: path.relative(process.cwd(), resultPath),
      triggered_at: result.triggered_at,
      completed_at: result.completed_at
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown server error";
    return Response.json(
      { status: "error", error: message },
      { status: 400 }
    );
  }
}
