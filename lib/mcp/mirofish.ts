import { getMcpServer } from "@/lib/mcp/registry";
import { resolveAuthToken } from "@/lib/mcp/auth";

// ---------------------------------------------------------------------------
// NECROSWARM REST client – wraps the Flask backend API (default: localhost:5001)
// ---------------------------------------------------------------------------

function baseUrl(): string {
  const server = getMcpServer("necroswarm");
  return (server.endpoint ?? "http://localhost:5001").replace(/\/+$/, "");
}

function headers(): Record<string, string> {
  const h: Record<string, string> = { "Content-Type": "application/json" };
  const token = resolveAuthToken("MIROFISH_API_KEY");
  if (token) {
    h["Authorization"] = `Bearer ${token}`;
  }
  return h;
}

async function mfFetch<T = unknown>(
  path: string,
  init?: RequestInit
): Promise<{ ok: boolean; data: T }> {
  const url = `${baseUrl()}${path}`;
  const res = await fetch(url, {
    ...init,
    headers: { ...headers(), ...(init?.headers as Record<string, string>) }
  });
  const data = (await res.json()) as T;
  return { ok: res.ok, data };
}

// ── Graph endpoints ──────────────────────────────────────────────────────────

export interface OntologyGenerateParams {
  simulation_requirement: string;
  project_name?: string;
  additional_context?: string;
}

export async function generateOntology(params: OntologyGenerateParams) {
  return mfFetch("/graph/ontology/generate", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function buildGraph(params: {
  project_id: string;
  graph_name?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  force?: boolean;
}) {
  return mfFetch("/graph/build", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function getTaskStatus(taskId: string) {
  return mfFetch(`/graph/task/${encodeURIComponent(taskId)}`);
}

export async function getGraphData(graphId: string) {
  return mfFetch(`/graph/data/${encodeURIComponent(graphId)}`);
}

export async function getProject(projectId: string) {
  return mfFetch(`/graph/project/${encodeURIComponent(projectId)}`);
}

export async function listProjects(limit?: number) {
  const q = limit ? `?limit=${limit}` : "";
  return mfFetch(`/graph/project/list${q}`);
}

// ── Simulation endpoints ─────────────────────────────────────────────────────

export async function createSimulation(params: {
  project_id: string;
  graph_id?: string;
  enable_twitter?: boolean;
  enable_reddit?: boolean;
}) {
  return mfFetch("/simulation/create", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function prepareSimulation(params: {
  simulation_id: string;
  force_regenerate?: boolean;
}) {
  return mfFetch("/simulation/prepare", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function getPreparationStatus(params: {
  task_id?: string;
  simulation_id?: string;
}) {
  return mfFetch("/simulation/prepare/status", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function startSimulation(params: {
  simulation_id: string;
  platform?: "twitter" | "reddit" | "parallel";
  max_rounds?: number;
  enable_graph_memory_update?: boolean;
  force?: boolean;
}) {
  return mfFetch("/simulation/start", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function stopSimulation(params: { simulation_id: string }) {
  return mfFetch("/simulation/stop", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function getSimulation(simulationId: string) {
  return mfFetch(`/simulation/${encodeURIComponent(simulationId)}`);
}

export async function getSimulationRunStatus(simulationId: string) {
  return mfFetch(
    `/simulation/${encodeURIComponent(simulationId)}/run-status`
  );
}

export async function getSimulationActions(
  simulationId: string,
  query?: { platform?: string; agent_id?: string; round?: number }
) {
  const params = new URLSearchParams();
  if (query?.platform) params.set("platform", query.platform);
  if (query?.agent_id) params.set("agent_id", query.agent_id);
  if (query?.round !== undefined) params.set("round", String(query.round));
  const qs = params.toString();
  return mfFetch(
    `/simulation/${encodeURIComponent(simulationId)}/actions${qs ? `?${qs}` : ""}`
  );
}

export async function getSimulationTimeline(simulationId: string) {
  return mfFetch(
    `/simulation/${encodeURIComponent(simulationId)}/timeline`
  );
}

export async function interviewAgent(params: {
  simulation_id: string;
  agent_id: string;
  question: string;
}) {
  return mfFetch("/simulation/interview", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

// ── Report endpoints ─────────────────────────────────────────────────────────

export async function generateReport(params: {
  simulation_id: string;
}) {
  return mfFetch("/report/generate", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function getReportGenerationStatus(params: {
  task_id?: string;
  simulation_id?: string;
}) {
  return mfFetch("/report/generate/status", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

export async function getReport(reportId: string) {
  return mfFetch(`/report/${encodeURIComponent(reportId)}`);
}

export async function getReportBySimulation(simulationId: string) {
  return mfFetch(
    `/report/by-simulation/${encodeURIComponent(simulationId)}`
  );
}

export async function chatWithReportAgent(params: {
  report_id: string;
  message: string;
  history?: Array<{ role: string; content: string }>;
}) {
  return mfFetch("/report/chat", {
    method: "POST",
    body: JSON.stringify(params)
  });
}

// ── Dispatcher: route MCP-style tool calls to the right function ─────────────

const TOOL_MAP: Record<string, (args: Record<string, unknown>) => Promise<{ ok: boolean; data: unknown }>> = {
  "necroswarm.ontology.generate": (a) => generateOntology(a as unknown as OntologyGenerateParams),
  "necroswarm.graph.build": (a) => buildGraph(a as unknown as Parameters<typeof buildGraph>[0]),
  "necroswarm.graph.task_status": (a) => getTaskStatus(a.task_id as string),
  "necroswarm.graph.data": (a) => getGraphData(a.graph_id as string),
  "necroswarm.project.get": (a) => getProject(a.project_id as string),
  "necroswarm.project.list": (a) => listProjects(a.limit as number | undefined),
  "necroswarm.simulation.create": (a) => createSimulation(a as Parameters<typeof createSimulation>[0]),
  "necroswarm.simulation.prepare": (a) => prepareSimulation(a as Parameters<typeof prepareSimulation>[0]),
  "necroswarm.simulation.prepare_status": (a) => getPreparationStatus(a as Parameters<typeof getPreparationStatus>[0]),
  "necroswarm.simulation.start": (a) => startSimulation(a as Parameters<typeof startSimulation>[0]),
  "necroswarm.simulation.stop": (a) => stopSimulation(a as Parameters<typeof stopSimulation>[0]),
  "necroswarm.simulation.get": (a) => getSimulation(a.simulation_id as string),
  "necroswarm.simulation.run_status": (a) => getSimulationRunStatus(a.simulation_id as string),
  "necroswarm.simulation.actions": (a) => getSimulationActions(a.simulation_id as string, a as Record<string, string>),
  "necroswarm.simulation.timeline": (a) => getSimulationTimeline(a.simulation_id as string),
  "necroswarm.simulation.interview": (a) => interviewAgent(a as Parameters<typeof interviewAgent>[0]),
  "necroswarm.report.generate": (a) => generateReport(a as Parameters<typeof generateReport>[0]),
  "necroswarm.report.generate_status": (a) => getReportGenerationStatus(a as Parameters<typeof getReportGenerationStatus>[0]),
  "necroswarm.report.get": (a) => getReport(a.report_id as string),
  "necroswarm.report.by_simulation": (a) => getReportBySimulation(a.simulation_id as string),
  "necroswarm.report.chat": (a) => chatWithReportAgent(a as Parameters<typeof chatWithReportAgent>[0])
};

export function listNECROSWARMTools(): string[] {
  return Object.keys(TOOL_MAP);
}

export async function executeNECROSWARMTool(
  tool: string,
  args: Record<string, unknown>
): Promise<{ ok: boolean; data: unknown }> {
  const handler = TOOL_MAP[tool];
  if (!handler) {
    return { ok: false, data: { error: `Unknown NECROSWARM tool: ${tool}` } };
  }
  try {
    return await handler(args);
  } catch (err) {
    return {
      ok: false,
      data: { error: (err as Error).message }
    };
  }
}
