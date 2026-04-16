# Memory Architecture Skill

## Purpose
Defines the 3-layer memory system that enables long-running coherence across OpenClaw agent sessions.

## Overview

The 3-layer memory system prevents **context window exhaustion** and **identity drift** — the two things that kill multi-agent systems.

| Layer | What It Is | When It Updates | Who Writes It |
|-------|-----------|-----------------|---------------|
| **Layer 1: Per-Message** | Every exchange is logged to daily memory files | Every session | Auto via heartbeat script |
| **Layer 2: Per-Agent** | Agent-specific working memory (AGENTS.md + per-agent files) | On role change, daily review | Each agent |
| **Layer 3: Global Long-Term** | MEMORY.md — the canonical source of truth | Weekly review + significant events | October |

## The 5-File Structure (Layer 2 Core)

Each agent workspace maintains these five files:

1. **MEMORY.md** — Long-term facts, infrastructure, decisions. The durable record.
2. **AGENTS.md** — Who the agents are, their roles, routing rules. Updated when roster changes.
3. **TOOLS.md** — Environment-specific notes. Camera names, SSH aliases, TTS preferences.
4. **SOUL.md** — Persona definition. Who the agent is, how it communicates, what it values.
5. **HEARTBEAT.md** — Operational state. Last active, current tasks, flags.

## Session Startup Sequence

1. Read `SOUL.md` — embody the persona
2. Read `USER.md` — know who you're helping
3. Read `memory/YYYY-MM-DD.md` (today + yesterday) — recent context
4. Read `MEMORY.md` — long-term reference

## Memory Compaction

When context runs high, run the compaction script:
```bash
bash skills/memory-architecture/scripts/compact.sh
```

Compaction merges daily notes into summaries, prunes redundant entries, and keeps the context lean.

## Files in This Skill

- `5-file-system.md` — Detailed breakdown of each file's purpose and update rules
- `layer-2-per-agent.md` — How each agent maintains its own working memory
- `compaction-strategy.md` — When and how to compact, thresholds, procedures
- `scripts/memory-write.sh` — Writes to daily memory files
- `scripts/compact.sh` — Compacts memory when context runs high

## Dependencies

- OpenClaw session management
- Write access to agent workspace directories
- Daily cron or manual trigger for compaction

## Model Considerations

The **qwen2.5:3b zombie problem**: qwen2.5:3b locks up on long context. Use **minimax-m2.7:cloud** as the workhorse model for any memory-intensive operations. The compaction scripts should run on minimax-m2.7:cloud, not smaller models.
