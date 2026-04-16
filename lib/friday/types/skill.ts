/**
 * Core type definitions for the F.R.I.D.A.Y skill system.
 *
 * Inspired by Paperclip's skill injection and plugin SDK patterns:
 * - Skills are self-describing units of capability
 * - Runtime context is injected via environment (not hardcoded)
 * - Each skill declares its own schema for validation
 */

export interface SkillManifest {
  /** Unique skill identifier (e.g., "system.diagnostics") */
  id: string;
  /** Human-readable name */
  name: string;
  /** Short description of what this skill does */
  description: string;
  /** Semantic version */
  version: string;
  /** Skill author */
  author?: string;
  /** Tags for discovery */
  tags?: string[];
  /** Required environment variables */
  requiredEnv?: string[];
  /** Skills this skill depends on */
  dependencies?: string[];
}

export type SkillStatus = "registered" | "loading" | "ready" | "error" | "disabled";

export interface SkillContext {
  /** Unique run/session ID for audit trail */
  runId: string;
  /** Agent identity */
  agentId: string;
  /** Structured logger */
  logger: SkillLogger;
  /** Key-value store scoped to this skill */
  store: SkillStore;
  /** Emit events for other skills to consume */
  emit: (event: string, payload: unknown) => void;
  /** Environment variables available to this skill */
  env: Record<string, string | undefined>;
}

export interface SkillLogger {
  info(msg: string, data?: Record<string, unknown>): void;
  warn(msg: string, data?: Record<string, unknown>): void;
  error(msg: string, data?: Record<string, unknown>): void;
  debug(msg: string, data?: Record<string, unknown>): void;
}

export interface SkillStore {
  get(key: string): Promise<unknown | undefined>;
  set(key: string, value: unknown): Promise<void>;
  delete(key: string): Promise<void>;
  list(prefix?: string): Promise<string[]>;
}

export interface SkillAction {
  /** Action name (unique within skill) */
  name: string;
  /** Description for agent discovery */
  description: string;
  /** JSON schema for input validation */
  inputSchema?: Record<string, unknown>;
  /** Execute the action */
  execute: (input: unknown, ctx: SkillContext) => Promise<SkillActionResult>;
}

export interface SkillActionResult {
  success: boolean;
  data?: unknown;
  error?: string;
}

export interface Skill {
  /** Skill metadata */
  manifest: SkillManifest;
  /** Actions this skill provides */
  actions: SkillAction[];
  /** Called when skill is loaded into the registry */
  setup?: (ctx: SkillContext) => Promise<void>;
  /** Called when skill is being unloaded */
  teardown?: (ctx: SkillContext) => Promise<void>;
  /** Event handlers */
  onEvent?: (event: string, payload: unknown, ctx: SkillContext) => Promise<void>;
}

export interface SkillRegistryEntry {
  skill: Skill;
  status: SkillStatus;
  loadedAt?: Date;
  error?: string;
}
