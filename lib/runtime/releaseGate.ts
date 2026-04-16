import { AuditReport, FinalReleaseArtifact, WorkerOutput } from "@/lib/runtime/types";

export function runReleaseGate(runId: string, audits: AuditReport[], workerOutput: WorkerOutput): FinalReleaseArtifact {
  const summary = audits.reduce(
    (acc, audit) => {
      acc[audit.status] += 1;
      return acc;
    },
    { pass: 0, warn: 0, fail: 0 }
  );

  const status: FinalReleaseArtifact["status"] = summary.fail > 0 ? "fail" : "pass";
  const next_action: FinalReleaseArtifact["next_action"] =
    summary.fail > 0 ? "manual_review" : summary.warn > 1 ? "revise" : "release";

  return {
    run_id: runId,
    status,
    next_action,
    model_used: workerOutput.model_used,
    estimated_cost_usd: workerOutput.estimated_cost_usd,
    audit_summary: summary
  };
}
