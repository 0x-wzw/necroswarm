/**
 * Skill Loader — Discovers and loads skills from the filesystem.
 *
 * Inspired by Paperclip's plugin loader pattern:
 * - Scans skill directories for manifests
 * - Validates skill structure before registration
 * - Supports both built-in and user-defined skills
 */

import { readdir, stat } from "node:fs/promises";
import { join } from "node:path";
import type { Skill } from "../types/index.js";
import type { SkillRegistry } from "./registry.js";

export interface LoaderOptions {
  /** Directories to scan for skills */
  skillDirs: string[];
  /** Registry to load skills into */
  registry: SkillRegistry;
}

export async function discoverSkills(dirs: string[]): Promise<string[]> {
  const paths: string[] = [];

  for (const dir of dirs) {
    try {
      const entries = await readdir(dir);
      for (const entry of entries) {
        const fullPath = join(dir, entry);
        const s = await stat(fullPath);
        if (s.isDirectory()) {
          paths.push(fullPath);
        }
      }
    } catch {
      // Directory doesn't exist or isn't readable — skip
    }
  }

  return paths;
}

export async function loadSkillModule(skillPath: string): Promise<Skill | null> {
  const indexPath = join(skillPath, "index.js");

  try {
    await stat(indexPath);
  } catch {
    // Try .ts for dev mode
    const tsPath = join(skillPath, "index.ts");
    try {
      await stat(tsPath);
      const mod = await import(tsPath);
      return validateSkillModule(mod);
    } catch {
      return null;
    }
  }

  const mod = await import(indexPath);
  return validateSkillModule(mod);
}

function validateSkillModule(mod: Record<string, unknown>): Skill | null {
  const skill = (mod.default ?? mod.skill) as Skill | undefined;

  if (!skill?.manifest?.id || !skill?.manifest?.name || !Array.isArray(skill?.actions)) {
    return null;
  }

  return skill;
}

export async function loadSkillsFromDirs(opts: LoaderOptions): Promise<void> {
  const paths = await discoverSkills(opts.skillDirs);

  for (const skillPath of paths) {
    const skill = await loadSkillModule(skillPath);
    if (skill) {
      opts.registry.register(skill);
    }
  }
}
