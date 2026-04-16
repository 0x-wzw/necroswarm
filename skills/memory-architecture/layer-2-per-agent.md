# Layer 2: Per-Agent Working Memory

Each agent in the swarm maintains its own working memory context. This is Layer 2 of the 3-layer memory architecture.

## Why Per-Agent Memory?

The swarm has shared knowledge (Layer 3: MEMORY.md) and session-level knowledge (Layer 1: daily logs). But each agent also needs its own working context — the things that matter specifically to that agent's role and current state.

Per-agent memory prevents:
- **Role confusion** — Halloween knows it's the Code Architect, not the Researcher
- **State leakage** — One agent's in-progress work doesn't pollute another's context
- **Redundant loading** — Each agent only loads what's relevant to its role

## What Goes in Per-Agent Memory

### Agent-Specific Context
- Current task focus and progress
- Pending technical decisions
- Code being worked on
- Research findings specific to that agent's domain

### Workspace Files
Each agent has a dedicated workspace:
```
~/.openclaw/workspace/         # October
~/.openclaw/workspace-halloween/  # Halloween
~/.openclaw/workspace-octoberxin/ # OctoberXin
```

Within each workspace, the 5-file structure applies:
- `MEMORY.md` — Agent's own long-term memory (separate from the global MEMORY.md)
- `AGENTS.md` — Agent's understanding of the roster
- `SOUL.md` — Agent's persona
- `TOOLS.md` — Agent's environment notes
- `HEARTBEAT.md` — Agent's operational state

### The Relationship Between Global and Local

```
Global MEMORY.md (Layer 3)
    ↓
    ↓ (read by all agents)
    ↓
Agent Workspace (Layer 2)
    ├── MEMORY.md  ← Agent's personal long-term notes
    ├── SOUL.md    ← Agent's persona
    ├── AGENTS.md  ← Agent's view of the roster
    ├── TOOLS.md   ← Agent's environment
    └── HEARTBEAT.md ← Agent's current state

    ↓
    ↓ (writes to)
    ↓
Daily Memory Files (Layer 1)
```

## Writing Per-Agent Memory

### When to Update

- **HEARTBEAT.md**: Every session start and end
- **MEMORY.md**: Weekly review + when significant agent-specific learning occurs
- **AGENTS.md**: When the agent learns something new about a teammate
- **SOUL.md**: Almost never (persona drift is a bug, not a feature)
- **TOOLS.md**: When the agent discovers a new tool or technique

### What to Record

**For Halloween (Code Architect):**
- Current code project state
- Technical decisions made and rationale
- Tools and techniques discovered
- Model behaviors observed (e.g., "qwen2.5:3b zombie problem")

**For OctoberXin (Researcher):**
- Research threads being explored
- Sources and findings
- Analysis frameworks being developed
- Challenges to conventional wisdom

**For October (Orchestrator):**
- Delegation patterns that work
- Routing rules that need adjustment
- Swarm coordination learnings

## Compaction

Per-agent memory compacts differently than global memory:

1. **Rotate HEARTBEAT.md**: Archive completed tasks, keep pending ones
2. **Summarize MEMORY.md**: Move detailed session notes to a "work log" file
3. **Prune AGENTS.md**: Remove stale information about teammates

The compaction script handles this:
```bash
bash skills/memory-architecture/scripts/compact.sh
```

## Anti-Patterns

### Don't
- Copy global MEMORY.md into agent MEMORY.md (duplication causes drift)
- Update SOUL.md based on a single session's mood
- Load teammate's HEARTBEAT.md unless specifically needed for coordination

### Do
- Reference global MEMORY.md when needed
- Keep HEARTBEAT.md lean — only active state
- Update AGENTS.md with genuine new information about teammates

## Model Considerations

Per-agent memory operations (reading, writing, compaction) should run on **minimax-m2.7:cloud**. Smaller models like qwen2.5:3b will go zombie on this kind of sustained contextual work.

This is a lesson paid for in frustration: the first time you try to compact memory with a small model, it locks up mid-operation.
