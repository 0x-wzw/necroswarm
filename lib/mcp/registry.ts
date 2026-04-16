export type MCPTransport = "stdio" | "https" | "deploy" | "necroswarm";

export interface MCPServerConfig {
  server_id: string;
  transport: MCPTransport;
  endpoint?: string;
  stdio?: {
    command: string;
    args?: string[];
  };
  auth_ref?: string;
}

const registry: Record<string, MCPServerConfig> = {
  local_fs: {
    server_id: "local_fs",
    transport: "stdio",
    stdio: {
      command: "npx",
      args: ["-y", "@modelcontextprotocol/server-filesystem", "."]
    },
    auth_ref: "MCP_TOKEN_LOCAL_FS"
  },
  remote_default: {
    server_id: "remote_default",
    transport: "https",
    endpoint: "https://example-mcp-server.invalid/mcp",
    auth_ref: "MCP_TOKEN_REMOTE_DEFAULT"
  },
  deploy_server: {
    server_id: "deploy_server",
    transport: "deploy",
    auth_ref: "DEPLOY_HOST"
  },
  necroswarm: {
    server_id: "necroswarm",
    transport: "necroswarm",
    endpoint: process.env.MIROFISH_API_URL ?? "http://localhost:5001",
    auth_ref: "MIROFISH_API_KEY"
  }
};

export function getMcpServer(serverId: string): MCPServerConfig {
  const config = registry[serverId];
  if (!config) {
    throw new Error(`MCP server not registered: ${serverId}`);
  }
  return config;
}

export function listMcpServers(): MCPServerConfig[] {
  return Object.values(registry);
}
