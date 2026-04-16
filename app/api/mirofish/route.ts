import { executeMirofishTool, listMirofishTools } from "@/lib/mcp/mirofish";

/**
 * POST /api/mirofish – Execute a MiroFish tool directly.
 *
 * Body: { "tool": "mirofish.simulation.create", "args": { ... } }
 *
 * This bypasses the full agent pipeline and calls MiroFish REST API
 * directly, useful for dashboards or lightweight orchestration.
 */
export async function POST(request: Request): Promise<Response> {
  try {
    const body = (await request.json()) as {
      tool?: string;
      args?: Record<string, unknown>;
    };

    if (!body.tool) {
      return Response.json(
        {
          status: "error",
          error: "Missing required field: tool",
          available_tools: listMirofishTools()
        },
        { status: 400 }
      );
    }

    const result = await executeMirofishTool(
      body.tool,
      body.args ?? {}
    );

    return Response.json({
      status: result.ok ? "ok" : "error",
      tool: body.tool,
      data: result.data
    });
  } catch (error) {
    const message =
      error instanceof Error ? error.message : "Unknown server error";
    return Response.json(
      { status: "error", error: message },
      { status: 500 }
    );
  }
}

/**
 * GET /api/mirofish – List available MiroFish tools.
 */
export async function GET(): Promise<Response> {
  return Response.json({
    server_id: "mirofish",
    tools: listMirofishTools()
  });
}
