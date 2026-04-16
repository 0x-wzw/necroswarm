# Quickstart: Set Up Your Own Agent Swarm

This guide walks you through setting up a multi-agent AI system similar to ours. We run on OpenClaw with 3 agents, but the principles apply to any agent framework.

## Prerequisites

- A Linux machine (we use AWS EC2)
- OpenClaw installed
- Ollama running with at least one capable model
- GitHub account with PAT for repos
- Basic comfort with CLI

## Step 1: Designate the Orchestrator

One agent must be the central coordination node. This agent:
- Receives all tasks from the human
- Classifies and routes to specialists
- Synthesizes output
- Keeps the human informed

In our setup: **October** is the orchestrator.

## Step 2: Set Up Ollama

```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull models
ollama pull minimax-m2.7:cloud    # Workhorse model
ollama pull qwen2.5:3b            # Optional: quick tasks only

# Expose Ollama (if needed for sub-agents)
# Edit /etc/ollama/ollama serve to bind 0.0.0.0
```

**Critical lesson**: qwen2.5:3b goes zombie on sustained context-heavy work. Use minimax-m2.7:cloud for everything that matters.

## Step 3: Set Up Agent Workspaces

Each agent needs its own workspace directory:

```bash
mkdir -p ~/.openclaw/workspace           # Main (orchestrator)
mkdir -p ~/.openclaw/workspace-halloween # Code architect
mkdir -p ~/.openclaw/workspace-octoberxin # Researcher
```

## Step 4: Implement the 5-File Structure

Each workspace needs these files:

```
workspace/
├── MEMORY.md      # Long-term facts
├── AGENTS.md      # Roster and routing
├── SOUL.md        # Persona
├── TOOLS.md       # Environment notes
├── HEARTBEAT.md   # Operational state
└── memory/
    └── YYYY-MM-DD.md  # Daily logs
```

See `skills/memory-architecture/5-file-system.md` for detailed descriptions.

## Step 5: Set Up Inter-Agent Communication

We use a relay server on port 18790:

```bash
# Deploy relay server
# See relay server documentation for your framework
```

Protocol:
```bash
curl -X POST http://localhost:18790/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"to":"agent-name","message":"task description"}'
```

## Step 6: Configure Routing Rules

Define who does what in AGENTS.md:

| Task Type | Primary Agent | Secondary |
|-----------|---------------|-----------|
| Tech/implementation | Code Architect | Orchestrator |
| Research/analysis | Researcher | Orchestrator |
| Coordination | Orchestrator | — |

Key constraint: **never wait on the human for approval**. Agents drive each other forward.

## Step 7: Set Up GitHub Access

```bash
git config --global credential.helper store
# When prompted, enter: https://GITHUB_PAT@github.com
```

Store PATs securely. We use repos under `0x-wzw` with PAT in git credential store.

## Step 8: Establish Session Startup Sequence

Every agent reads at session start:

1. `SOUL.md` — embody the persona
2. `USER.md` — know who you're helping
3. `memory/YYYY-MM-DD.md` (today + yesterday) — recent context
4. `MEMORY.md` — long-term reference

## Step 9: Set Up Memory Compaction

Memory grows. Plan for compaction:

```bash
# Weekly compaction (run on minimax-m2.7:cloud)
0 3 * * 0 cd ~/.openclaw/workspace && bash skills/memory-architecture/scripts/compact.sh
```

Warning signs that compaction is needed:
- Model starts repeating itself
- Agent forgets recent context mid-conversation
- "Context window exceeded" errors

See `skills/memory-architecture/compaction-strategy.md` for full details.

## Step 10: Document Everything

Start a repo like this one:
```
agent-swarm-protocol/
├── README.md
├── skills/
├── philosophy/
├── agents/
└── docs/
```

Document as you learn. Future-you will thank present-you.

## Model Selection Guide

| Task | Model |
|------|-------|
| Orchestration, routing | minimax-m2.7:cloud |
| Code, infrastructure | minimax-m2.7:cloud |
| Memory compaction | minimax-m2.7:cloud (NOT qwen2.5:3b) |
| Research, analysis | minimax-m2.7:cloud |
| Quick one-off queries | qwen2.5:3b (if available, handle with care) |

**Never**: Run memory compaction, sustained reasoning, or multi-step tasks on qwen2.5:3b. It will go zombie.

## Anti-Patterns to Avoid

1. **Don't skip the 5-file structure** — It's not bureaucracy, it's sanity
2. **Don't let context run unchecked** — Compaction is not optional
3. **Don't wait on the human for approval** — Keep them informed, not bottlenecks
4. **Don't use small models for heavy lifting** — See: qwen2.5:3b zombie problem
5. **Don't skip persona reinforcement** — Read SOUL.md every session

## What We Learned in 2 Days

1. **The zombie problem**: qwen2.5:3b locks up. minimax-m2.7:cloud is the workhorse.
2. **Context windows are real**: Without layered memory, coherence breaks.
3. **3 agents works**: Enough specialization, not too much overhead.
4. **Forgiveness matters**: Perfect memory is a curse. Let things go.

See `docs/LESSONS.md` for the full list.

## Getting Help

- OpenClaw docs: Check your installation
- Relay server: Port 18790 (if using our setup)
- This repo: https://github.com/0x-wzw/agent-swarm-protocol

Good luck. Build something that can forgive.
