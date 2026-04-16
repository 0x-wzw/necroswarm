import { spawn, execSync } from "node:child_process";
import type { Adapter, AdapterInvokeParams, AdapterResult } from "../types/index.js";

export interface ProcessAdapterConfig {
  command: string;
  args?: string[];
  workDir?: string;
  env?: Record<string, string>;
  timeoutMs?: number;
  maxBytes?: number;
}

export function createProcessAdapter(config: ProcessAdapterConfig): Adapter {
  const MAX_BYTES = config.maxBytes ?? 1024 * 1024 * 5; // 5MB limit default

  return {
    type: "process",
    name: `process:${config.command}`,

    async invoke(params: AdapterInvokeParams): Promise<AdapterResult> {
      return new Promise((resolve) => {
        const proc = spawn(config.command, config.args ?? [], {
          cwd: config.workDir,
          env: { ...process.env, ...config.env, FRIDAY_RUN_ID: params.runId },
          stdio: ["pipe", "pipe", "pipe"],
          timeout: config.timeoutMs ?? 60_000,
        });

        let stdout = "";
        let stderr = "";

        proc.stdout.on("data", (data: Buffer) => {
          if (stdout.length < MAX_BYTES) {
            stdout += data.toString();
            if (stdout.length >= MAX_BYTES) stdout += "\n...[TRUNCATED_OOM_PROTECTION]";
          }
        });

        proc.stderr.on("data", (data: Buffer) => {
          if (stderr.length < MAX_BYTES) {
            stderr += data.toString();
            if (stderr.length >= MAX_BYTES) stderr += "\n...[TRUNCATED_OOM_PROTECTION]";
          }
        });

        proc.stdin.write(params.prompt);
        proc.stdin.end();

        proc.on("close", (code) => {
          if (code === 0) {
            resolve({ success: true, output: stdout });
          } else {
            resolve({
              success: false,
              output: stdout,
              error: stderr || `Process exited with code ${code}`,
            });
          }
        });

        proc.on("error", (err) => {
          resolve({ success: false, output: "", error: err.message });
        });
      });
    },

    async healthCheck() {
      try {
        execSync(`which ${config.command}`, { stdio: "ignore" });
        return true;
      } catch {
        return false;
      }
    },
  };
}
