---
name: x-interact
description: Interact with X.com (Twitter) via Tavily web search and extraction. Use when you need to read tweets, search X content, or analyze posts. Requires Tavily API key (free tier works). Configure mcporter with tavily MCP server. X.com blocks direct extraction (403) — Tavily's search index bypasses this.
---

# X.com Interact via Tavily

Tavily is configured as MCP server `tavily` in mcporter. Use it to search and extract X.com content.

## Setup

```bash
mcporter config add tavily https://mcp.tavily.com/mcp/?tavilyApiKey=<YOUR_KEY>
```

## Operations

### Search X.com

```bash
# Find tweets by user + keyword
mcporter call tavily.tavily_search query="from:username keyword" max_results=5

# Get recent tweets from a user
mcporter call tavily.tavily_search query="site:x.com username" max_results=10 search_depth="basic"

# Find tweets on a topic
mcporter call tavily.tavily_search query="from:elonmusk tesla" max_results=5
```

### Extract from a URL

```bash
# Extract article/news content (not X.com itself)
mcporter call tavily.tavily_extract urls='["https://example.com/article"]'
```

### Deep Research on a Topic

```bash
mcporter call tavily.tavily_research query="AI agents crypto DeFi 2026" depth="medium" max_results=10
```

## Notes

- X.com returns 403 on direct fetch — Tavily search index works around this
- Tavily extracts snippets from search results; for full tweet text, ask Z to paste
- Rate limit: 20 req/min free tier
- Works for profiles, tweet URLs, and topics via search index
