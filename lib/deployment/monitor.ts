import { resolveAuthToken } from "@/lib/mcp/auth";

export interface MonitorCheckResult {
  deploy_id: string;
  healthy: boolean;
  checked_at: string;
  status_code?: number;
  latency_ms: number;
}

export async function runMonitorCheck(
  deployId: string,
  hostEnvRef: string,
  healthPath: string
): Promise<MonitorCheckResult> {
  const checkedAt = new Date().toISOString();
  const host = resolveAuthToken(hostEnvRef);

  if (!host) {
    return {
      deploy_id: deployId,
      healthy: false,
      checked_at: checkedAt,
      latency_ms: 0
    };
  }

  const url = `http://${host}${healthPath}`;
  const start = Date.now();

  try {
    const response = await fetch(url, { signal: AbortSignal.timeout(5000) });
    const latency_ms = Date.now() - start;
    return {
      deploy_id: deployId,
      healthy: response.ok,
      checked_at: checkedAt,
      status_code: response.status,
      latency_ms
    };
  } catch {
    return {
      deploy_id: deployId,
      healthy: false,
      checked_at: checkedAt,
      latency_ms: Date.now() - start
    };
  }
}
