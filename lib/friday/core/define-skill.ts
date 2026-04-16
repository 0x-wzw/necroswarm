/**
 * Skill Definition Helper — Convenience function for defining skills.
 *
 * Inspired by Paperclip's definePlugin() pattern from their SDK.
 * Provides type-safe skill construction with sensible defaults.
 */

import type { Skill, SkillManifest, SkillAction, SkillContext } from "../types/index.js";

export interface DefineSkillOptions {
  manifest: SkillManifest;
  actions?: SkillAction[];
  setup?: (ctx: SkillContext) => Promise<void>;
  teardown?: (ctx: SkillContext) => Promise<void>;
  onEvent?: (event: string, payload: unknown, ctx: SkillContext) => Promise<void>;
}

export function defineSkill(opts: DefineSkillOptions): Skill {
  return {
    manifest: {
      version: "0.1.0",
      ...opts.manifest,
    },
    actions: opts.actions ?? [],
    setup: opts.setup,
    teardown: opts.teardown,
    onEvent: opts.onEvent,
  };
}
