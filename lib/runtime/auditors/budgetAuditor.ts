import { AuditReport, BotPackage, PreflightReport, TaskSpec } from "@/lib/runtime/types";

export function runBudgetAuditor(taskSpec: TaskSpec, preflight: PreflightReport, botPackage: BotPackage): AuditReport {
  const findings: string[] = [];

  if (taskSpec.budget.max_usd > 5) {
    findings.push("Task budget exceeds hard cap of $5.");
  }

  if (preflight.recommended_caps.max_usd > 5) {
    findings.push("Preflight recommended cap exceeds hard cap.");
  }

  if (taskSpec.risk_level === "high" && botPackage.model === "openai:gpt-4o-mini") {
    findings.push("Model may be underpowered for high-risk task.");
  }

  const status: AuditReport["status"] = findings.length === 0 ? "pass" : findings.some((f) => f.includes("exceeds hard cap")) ? "fail" : "warn";

  return {
    audit_type: "budget",
    status,
    score: status === "pass" ? 1 : status === "warn" ? 0.7 : 0.3,
    findings,
    recommendations:
      status === "pass"
        ? ["Budget and model fit checks passed."]
        : ["Lower token caps and/or escalate model according to task risk profile."]
  };
}
