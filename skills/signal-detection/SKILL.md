---
name: signal-detection
description: |
  Always-on entity extraction running in parallel on every message.
  Extracts entities, preferences, and patterns. Classifies signals by
  memory priority (HIGH/MEDIUM/LOW) and generates save recommendations.
version: 1.0.0
author: Z Teoh (0x-wzw)
license: MIT
category: agent-orchestration
icon: 👁️
tags:
  - signal-detection
  - entity-extraction
  - memory
  - preferences
scripts:
  - scripts/detect.py
---

# 👁️ Signal Detection — Always-On Entity Extraction

> Every message. Every time. In parallel. No blocking. No permission needed.

## What It Does

Extracts three signal types from every message:
1. **Entities** — named entities (people, projects, URLs, tools, models)
2. **Preferences** — user corrections, directives, stated preferences
3. **Patterns** — recurring themes that suggest skill creation or debugging

Classifies each signal as HIGH (save now), MEDIUM (save if durable), or LOW (skip).

## Active Script

```bash
# Detect signals in a message
python ~/.hermes/skills/agent-orchestration/signal-detection/scripts/detect.py "Update voidtether readme and include gbrain"

# JSON output for programmatic use
python ~/.hermes/skills/agent-orchestration/signal-detection/scripts/detect.py --json "I prefer autonomous execution"

# Returns: entities, preferences, signal classification, memory actions
```

## Memory Decision Matrix

| Signal Strength | Content Type | Action |
|---|---|---|
| **HIGH** | User correction, explicit preference, decision | `memory add` immediately |
| **MEDIUM** | Useful entity, project context | `memory add` if durable |
| **LOW** | Passing reference, ambiguous | Skip — resurfaces if important |

## How to Use

1. **On every message**, run `detect.py` mentally or via terminal
2. **For HIGH signals**, immediately save to `memory`
3. **For MEDIUM signals**, save if the fact is durable (won't expire)
4. **For LOW signals**, skip — it'll resurface if it matters

## What NOT to Do

- ❌ Block the main response for signal detection
- ❌ Save every entity mentioned (only durable facts)
- ❌ Run detect.py as a separate tool call on every turn (it's a cognitive pattern)
- ❌ Duplicate what memory already knows
- ❌ Treat this as GBrain's knowledge compounder (we're a swarm, not a brain)

## Difference from GBrain

GBrain's `signal-detector` writes to a PGLite knowledge base with entity pages and 25 MCP tools. Ours writes to Hermes memory (2.2KB key-value). GBrain compounds knowledge over months. We extract signal for *this session* and *durable preferences* only. Different scope, different storage.