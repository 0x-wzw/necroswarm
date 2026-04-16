import { randomUUID } from "node:crypto";
import path from "node:path";

import { buildBotPackage } from "@/lib/runtime/botBuilder";
import { ensureRunArtifactDir, writeArtifact } from "@/lib/runtime/artifacts";
import { runBudgetGate } from "@/lib/runtime/budgetGate";
import { pickModel } from "@/lib/runtime/modelPicker";
import { orchestrate } from "@/lib/runtime/orchestrator";
import { runReleaseGate } from "@/lib/runtime/releaseGate";
import { assertValidSchema } from "@/lib/runtime/validator";
import { runWorker } from "@/lib/runtime/worker";
import { runBudgetAuditor } from "@/lib/runtime/auditors/budgetAuditor";
import { runQualityAuditor } from "@/lib/runtime/auditors/qualityAuditor";
import { runRiskAuditor } from "@/lib/runtime/auditors/riskAuditor";
import { runSpecAuditor } from "@/lib/runtime/auditors/specAuditor";
import { AuditReport, BotPackage, PreflightReport, TaskSpec, WorkerOutput } from "@/lib/runtime/types";

const HARD_MAX_USD = 5;

export async function POST(request: Request): Promise<Response> {
  try {
    const body: unknown = await request.json();
    assertValidSchema<TaskSpec>("taskSpec", body);

    const runId = randomUUID();
    const artifactsDir = await ensureRunArtifactDir(runId);

    const plan = orchestrate(
      {
        ...body,
        budget: {
          ...body.budget,
          max_usd: Math.min(body.budget.max_usd, HARD_MAX_USD)
        }
      },
      runId
    );

    const preflight = runBudgetGate(plan);
    assertValidSchema<PreflightReport>("preflight", preflight);

    const selectedModel = pickModel({
      plan,
      preflight
    });

    const botPackage = buildBotPackage(plan, selectedModel);
    assertValidSchema<BotPackage>("botPackage", botPackage);

    const workerOutput = await runWorker({
      taskSpec: plan.normalized_task,
      botPackage,
      artifactsDir,
      maxOutputTokens: Math.min(preflight.recommended_caps.max_output_tokens, plan.normalized_task.budget.max_output_tokens)
    });

    const audits: AuditReport[] = [
      runSpecAuditor(plan.normalized_task, botPackage, workerOutput),
      runQualityAuditor(workerOutput),
      runRiskAuditor(plan.normalized_task, workerOutput),
      runBudgetAuditor(plan.normalized_task, preflight, botPackage)
    ];

    for (const audit of audits) {
      assertValidSchema<AuditReport>("auditReport", audit);
    }

    const escalatedModel = pickModel({
      plan,
      preflight,
      audits
    });

    const finalRelease = runReleaseGate(runId, audits, {
      ...workerOutput,
      model_used: escalatedModel
    } as WorkerOutput);

    const taskSpecPath = await writeArtifact(artifactsDir, "task_spec.json", plan.normalized_task);
    const preflightPath = await writeArtifact(artifactsDir, "preflight_report.json", preflight);
    const botPackagePath = await writeArtifact(artifactsDir, "bot_package.json", botPackage);
    const workerPath = await writeArtifact(artifactsDir, "worker_output.json", workerOutput);
    const auditsPath = await writeArtifact(artifactsDir, "audit_reports.json", audits);
    const finalPath = await writeArtifact(artifactsDir, "final_release.json", finalRelease);

    return Response.json({
      run_id: runId,
      status: finalRelease.status,
      final_artifact_ref: path.relative(process.cwd(), finalPath),
      audit_refs: [path.relative(process.cwd(), auditsPath)],
      model_used: escalatedModel,
      estimated_cost_usd: workerOutput.estimated_cost_usd,
      artifact_refs: {
        task_spec: path.relative(process.cwd(), taskSpecPath),
        preflight: path.relative(process.cwd(), preflightPath),
        bot_package: path.relative(process.cwd(), botPackagePath),
        worker_output: path.relative(process.cwd(), workerPath)
      }
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown server error";
    return Response.json(
      {
        status: "error",
        error: message
      },
      { status: 400 }
    );
  }
}
