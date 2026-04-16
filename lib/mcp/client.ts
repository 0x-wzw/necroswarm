import { getMcpServer } from "@/lib/mcp/registry";
import { resolveAuthToken } from "@/lib/mcp/auth";
import { executeNECROSWARMTool } from "@/lib/mcp/necroswarm";

export interface MCPToolCallRequest {
  server_id: string;
  tool: string;
  args: Record<string, unknown>;
}

export interface MCPToolCallResponse {
  ok: boolean;
  data: unknown;
  transport: "stdio" | "https" | "necroswarm";
}

export async function executeMcpTool(request: MCPToolCallRequest): Promise<MCPToolCallResponse> {
  const server = getMcpServer(request.server_id);
  const token = resolveAuthToken(server.auth_ref);

  if (server.transport === "necroswarm") {
    const result = await executeNECROSWARMTool(request.tool, request.args);
    return {
      ok: result.ok,
      transport: "necroswarm",
      data: result.data
    };
  }

  if (server.transport === "https") {
    return {
      ok: true,
      transport: "https",
      data: {
        stub: true,
        note: "HTTPS MCP execution is stubbed in this implementation.",
        server_id: request.server_id,
        tool: request.tool,
        args: request.args,
        auth_present: Boolean(token)
      }
    };
  }

  return {
    ok: true,
    transport: "stdio",
    data: {
      stub: true,
      note: "stdio MCP execution is stubbed in this implementation.",
      server_id: request.server_id,
      tool: request.tool,
      args: request.args,
      auth_present: Boolean(token)
    }
  };
}
