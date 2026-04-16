import { AuditReport, WorkerOutput } from "@/lib/runtime/types";

export function runQualityAuditor(workerOutput: WorkerOutput): AuditReport {
  const findings: string[] = [];

  if (workerOutput.content.length < 60) {
    findings.push("Output is likely too brief for production usage.");
  }

  if (!/\n|\-|\d+\./.test(workerOutput.content)) {
    findings.push("Output structure may be hard to read.");
  }

  const pass = findings.length === 0;

  return {
    audit_type: "quality",
    status: pass ? "pass" : "warn",
    score: pass ? 0.95 : 0.7,
    findings,
    recommendations: pass ? ["Quality is acceptable."] : ["Improve structure and readability with headings or bullets."]
  };
}
