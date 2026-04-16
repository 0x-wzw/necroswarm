/**
 * Adapter types for pluggable agent execution.
 *
 * Inspired by Paperclip's adapter pattern where agents can run as
 * different runtimes (Claude CLI, HTTP webhook, shell process, etc.)
 * without changing core orchestration logic.
 */

export type AdapterType = "claude_local" | "process" | "http" | "custom";

export interface AdapterConfig {
  type: AdapterType;
  /** Model to use (for LLM adapters) */
  model?: string;
  /** Working directory */
  workDir?: string;
  /** Environment variables to inject */
  env?: Record<string, string>;
  /** Timeout in milliseconds */
  timeoutMs?: number;
  /** Adapter-specific configuration */
  options?: Record<string, unknown>;
}

export interface AdapterInvokeParams {
  /** The prompt/instruction to send */
  prompt: string;
  /** Context from previous runs */
  sessionContext?: string;
  /** Skills available to the agent */
  availableSkills?: string[];
  /** Run ID for tracing */
  runId: string;
}

export interface AdapterResult {
  success: boolean;
  output: string;
  /** Tokens/cost info for budget tracking */
  usage?: {
    inputTokens?: number;
    outputTokens?: number;
    costUsd?: number;
  };
  error?: string;
}

export interface Adapter {
  type: AdapterType;
  name: string;
  invoke(params: AdapterInvokeParams): Promise<AdapterResult>;
  healthCheck?(): Promise<boolean>;
}
