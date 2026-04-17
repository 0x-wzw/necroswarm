---
name: brain-first
description: |
  Check memory and session history BEFORE making external API calls.
  Convention: memory → session_search → web_search. Saves tokens and
  time by avoiding redundant lookups. Includes executable cache-check script.
version: 1.0.0
author: Z Teoh (0x-wzw)
license: MIT
category: agent-orchestration
icon: 🧠
tags:
  - memory
  - cache
  - efficiency
  - convention
scripts:
  - scripts/brain_check.py
---

# 🧠 Brain-First Convention — Check Memory Before External Calls

> "Have we been here before?" — Ask this BEFORE every web_search, before every API call.

## What It Does

A priority rule: **memory → session_search → web_search**. Checks local knowledge before making expensive external calls. Includes an executable script that searches memory files and session transcripts.

## Active Script

```bash
# Check if information exists locally before web_search
python ~/.hermes/skills/agent-orchestration/brain-first/scripts/brain_check.py "voidtether github url"

# JSON output
python ~/.hermes/skills/agent-orchestration/brain-first/scripts/brain_check.py --json "ollama cloud models"

# Source-only (don't show content, just whether it exists)
python ~/.hermes/skills/agent-orchestration/brain-first/scripts/brain_check.py --source-only "telegram bot token"

# Exit 0 = found locally (skip external call), Exit 1 = not found (proceed with web_search)
```

## The Convention

### Before ANY external call, follow this order:

```
1. Check memory → Found? → Use it. Done.
2. Check session_search → Found? → Recall context. Use it.
3. Only THEN → web_search / web_extract / browser
```

## What Counts as "External"

| Call Type | Cost | Brain-First? |
|---|---|---|
| `web_search` | High | ✅ Check memory first |
| `web_extract` | High | ✅ Check memory first |
| `browser_navigate` | Very High | ✅ Check memory first |
| `mcp_tavily_*` | Medium | ✅ Check memory first |
| `memory` / `session_search` | Free/Local | 🟢 Already internal |
| `terminal` / `read_file` | Local | 🟢 Already internal |

## When to Save

- **HIGH signal** (user correction, preference, decision) → `memory add` immediately
- **MEDIUM signal** (useful entity, project context) → `memory add` if durable
- **LOW signal** (passing reference) → skip

## Anti-Patterns

- ❌ Web searching for facts already in memory
- ❌ Skipping memory check for "obvious" questions
- ❌ Saving transient information to memory (pollutes the cache)

## Difference from GBrain

GBrain checks a PGLite knowledge base with hybrid RAG. We check a 2.2KB key-value memory and session transcripts. Simpler, but same principle: **don't do expensive work when you already have the answer.**