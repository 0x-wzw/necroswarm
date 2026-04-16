import { runMonitorCheck } from "@/lib/deployment/monitor";

interface MonitorRequest {
  deploy_id: string;
  host_env_ref: string;
  health_path: string;
}

export async function POST(request: Request): Promise<Response> {
  try {
    const body = (await request.json()) as MonitorRequest;

    if (!body.deploy_id || !body.host_env_ref || !body.health_path) {
      return Response.json(
        { status: "error", error: "Missing required fields: deploy_id, host_env_ref, health_path" },
        { status: 400 }
      );
    }

    const result = await runMonitorCheck(body.deploy_id, body.host_env_ref, body.health_path);

    return Response.json(result, { status: result.healthy ? 200 : 503 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Unknown server error";
    return Response.json(
      { status: "error", error: message },
      { status: 400 }
    );
  }
}
