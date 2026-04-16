---
name: mcporter
description: MCP server management for OpenClaw. Configure, auth, and call MCP servers/tools directly (HTTP or stdio). Use mcporter to add MCP servers, generate CLI/type bindings, and call tools. Covers ad-hoc servers, config edits, and CLI generation. Required for Tavily, and any other MCP-connected services.
---

# MCPorter Skill

Manage MCP (Model Context Protocol) servers and call their tools.

## Prerequisites

```bash
# Verify mcporter is available
mcporter --version

# If not installed
npm install -g @openclawai/mcporter
```

## Configure an MCP Server

### HTTP Server (e.g., Tavily)

```bash
mcporter config add tavily "https://mcp.tavily.com/mcp/?tavilyApiKey=${TAVILY_API_KEY}"
```

### stdio Server (local)

```bash
mcporter config add my-server "npx --yes @some/mcp-server"
```

## List Configured Servers

```bash
mcporter config list
```

## Call a Tool

```bash
# Call tavily search
mcporter call tavily.tavily_search query="AI agents 2026" max_results=5

# Call tavily extract
mcporter call tavily.tavily_extract urls='["https://example.com"]'
```

## Common MCP Servers

| Server | URL/Command | Tools |
|--------|-------------|-------|
| Tavily | `https://mcp.tavily.com/mcp/?...` | tavily_search, tavily_extract, tavily_research |
| Filesystem | `npx -y @modelcontextprotocol/server-filesystem` | read_file, write_file, list_directory |
| Brave Search | `npx -y @modelcontextprotocol/server-brave-search` | search, highlights |

## Validate Config

```bash
mcporter validate
```

## Notes

- HTTP servers use URL with API key param
- stdio servers start a subprocess
- Each server exposes different tools — check their docs
- Tools are called as `serverName.toolName` in mcporter call
