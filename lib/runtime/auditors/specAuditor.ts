import { AuditReport, BotPackage, TaskSpec, WorkerOutput } from "@/lib/runtime/types";

export function runSpecAuditor(taskSpec: TaskSpec, botPackage: BotPackage, workerOutput: WorkerOutput): AuditReport {
  const findings: string[] = [];

  if (!workerOutput.content.trim()) {
    findings.push("Worker output is empty.");
  }

  for (const criterion of taskSpec.acceptance_criteria) {
    if (!workerOutput.content.toLowerCase().includes(criterion.toLowerCase().slice(0, 10))) {
      findings.push(`Output does not clearly reflect criterion: ${criterion}`);
    }
  }

  if (!botPackage.tests.length) {
    findings.push("Bot package does not include acceptance tests.");
  }

  const pass = findings.length === 0;

  return {
    audit_type: "spec",
    status: pass ? "pass" : "warn",
    score: pass ? 1 : Math.max(0.4, 1 - findings.length * 0.1),
    findings,
    recommendations: pass ? ["No spec issues found."] : ["Revise output to explicitly satisfy each acceptance criterion."]
  };
}
