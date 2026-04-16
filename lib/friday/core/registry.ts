/**
 * Skill Registry — Central registry for discovering, loading, and managing skills.
 *
 * Inspired by Paperclip's plugin system:
 * - Skills are registered with manifests
 * - Dependency resolution before activation
 * - Lifecycle hooks (setup/teardown)
 * - Event bus for cross-skill communication
 */

import type {
  Skill,
  SkillRegistryEntry,
  SkillStatus,
  SkillContext,
  SkillAction,
  SkillActionResult,
} from "../types/index.js";
import { createSkillContext } from "./context.js";

export class SkillRegistry {
  private skills = new Map<string, SkillRegistryEntry>();
  private eventListeners = new Map<string, Set<string>>();

  get size(): number {
    return this.skills.size;
  }

  register(skill: Skill): void {
    if (this.skills.has(skill.manifest.id)) {
      throw new Error(`Skill "${skill.manifest.id}" is already registered`);
    }

    this.skills.set(skill.manifest.id, {
      skill,
      status: "registered",
    });
  }

  async load(skillId: string): Promise<void> {
    const entry = this.skills.get(skillId);
    if (!entry) {
      throw new Error(`Skill "${skillId}" not found in registry`);
    }

    if (entry.status === "ready") return;

    // Check dependencies
    const deps = entry.skill.manifest.dependencies ?? [];
    for (const dep of deps) {
      const depEntry = this.skills.get(dep);
      if (!depEntry) {
        throw new Error(`Skill "${skillId}" depends on "${dep}" which is not registered`);
      }
      if (depEntry.status !== "ready") {
        await this.load(dep);
      }
    }

    entry.status = "loading";

    try {
      if (entry.skill.setup) {
        const ctx = this.createContext(skillId);
        await entry.skill.setup(ctx);
      }
      entry.status = "ready";
      entry.loadedAt = new Date();
    } catch (err) {
      entry.status = "error";
      entry.error = err instanceof Error ? err.message : String(err);
      throw err;
    }
  }

  async loadAll(): Promise<{ loaded: string[]; failed: Array<{ id: string; error: string }> }> {
    const loaded: string[] = [];
    const failed: Array<{ id: string; error: string }> = [];

    for (const [id] of this.skills) {
      try {
        await this.load(id);
        loaded.push(id);
      } catch (err) {
        failed.push({
          id,
          error: err instanceof Error ? err.message : String(err),
        });
      }
    }

    return { loaded, failed };
  }

  async unload(skillId: string): Promise<void> {
    const entry = this.skills.get(skillId);
    if (!entry) return;

    if (entry.skill.teardown && entry.status === "ready") {
      const ctx = this.createContext(skillId);
      await entry.skill.teardown(ctx);
    }

    entry.status = "disabled";
  }

  getSkill(skillId: string): Skill | undefined {
    return this.skills.get(skillId)?.skill;
  }

  getStatus(skillId: string): SkillStatus | undefined {
    return this.skills.get(skillId)?.status;
  }

  listSkills(): SkillRegistryEntry[] {
    return Array.from(this.skills.values());
  }

  listReady(): Skill[] {
    return Array.from(this.skills.values())
      .filter((e) => e.status === "ready")
      .map((e) => e.skill);
  }

  findAction(skillId: string, actionName: string): SkillAction | undefined {
    const skill = this.getSkill(skillId);
    return skill?.actions.find((a) => a.name === actionName);
  }

  async executeAction(
    skillId: string,
    actionName: string,
    input: unknown
  ): Promise<SkillActionResult> {
    const entry = this.skills.get(skillId);
    if (!entry) {
      return { success: false, error: `Skill "${skillId}" not found` };
    }
    if (entry.status !== "ready") {
      return { success: false, error: `Skill "${skillId}" is not ready (status: ${entry.status})` };
    }

    const action = entry.skill.actions.find((a) => a.name === actionName);
    if (!action) {
      return { success: false, error: `Action "${actionName}" not found in skill "${skillId}"` };
    }

    const ctx = this.createContext(skillId);
    try {
      return await action.execute(input, ctx);
    } catch (err) {
      return {
        success: false,
        error: err instanceof Error ? err.message : String(err),
      };
    }
  }

  async emit(event: string, payload: unknown): Promise<void> {
    for (const [id, entry] of this.skills) {
      if (entry.status === "ready" && entry.skill.onEvent) {
        const ctx = this.createContext(id);
        try {
          await entry.skill.onEvent(event, payload, ctx);
        } catch {
          // Event handlers should not crash the bus
        }
      }
    }
  }

  private createContext(skillId: string): SkillContext {
    return createSkillContext({
      skillId,
      emit: (event, payload) => this.emit(event, payload),
    });
  }
}
