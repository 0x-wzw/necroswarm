import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

export async function ensureRunArtifactDir(runId: string): Promise<string> {
  const artifactsDir = path.join(process.cwd(), "artifacts", runId);
  await mkdir(artifactsDir, { recursive: true });
  return artifactsDir;
}

export async function writeArtifact(artifactsDir: string, filename: string, data: unknown): Promise<string> {
  const outputPath = path.join(artifactsDir, filename);
  await writeFile(outputPath, JSON.stringify(data, null, 2), "utf8");
  return outputPath;
}
