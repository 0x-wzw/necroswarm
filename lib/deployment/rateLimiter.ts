import { DeployEnv } from "@/lib/deployment/types";

const WINDOW_MS = 60 * 60 * 1000; // 1 hour
const MAX_DEPLOYS_PER_WINDOW = 5;

interface WindowState {
  count: number;
  window_start_ms: number;
}

const state: Record<string, WindowState> = {};

function getWindow(env: string): WindowState {
  const now = Date.now();
  const current = state[env];
  if (!current || now - current.window_start_ms >= WINDOW_MS) {
    state[env] = { count: 0, window_start_ms: now };
  }
  return state[env];
}

export function checkRateLimit(env: DeployEnv): { allowed: boolean; reason?: string } {
  const window = getWindow(env);
  if (window.count >= MAX_DEPLOYS_PER_WINDOW) {
    return {
      allowed: false,
      reason: `Rate limit exceeded: max ${MAX_DEPLOYS_PER_WINDOW} deployments per hour for env '${env}'.`
    };
  }
  return { allowed: true };
}

export function recordDeploy(env: string): void {
  const window = getWindow(env);
  window.count += 1;
}
