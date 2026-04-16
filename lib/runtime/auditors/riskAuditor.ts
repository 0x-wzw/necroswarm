import { AuditReport, TaskSpec, WorkerOutput } from "@/lib/runtime/types";

const BANNED_PATTERNS = [/api[_-]?key/i, /password/i, /secret/i, /token\s*[:=]/i];

export function runRiskAuditor(taskSpec: TaskSpec, workerOutput: WorkerOutput): AuditReport {
  const findings: string[] = [];

  if (taskSpec.risk_level === "high") {
    findings.push("High-risk task requires manual review before release.");
  }

  for (const pattern of BANNED_PATTERNS) {
    if (pattern.test(workerOutput.content)) {
      findings.push("Potential secret leakage detected in worker output.");
      break;
    }
  }

  const status: AuditReport["status"] = findings.some((f) => f.includes("leakage")) ? "fail" : findings.length ? "warn" : "pass";

  return {
    audit_type: "risk",
    status,
    score: status === "pass" ? 0.95 : status === "warn" ? 0.6 : 0.2,
    findings,
    recommendations:
      status === "pass"
        ? ["No immediate risk findings."]
        : ["Remove sensitive content and require human approval for high-risk tasks."]
  };
}
