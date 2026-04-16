# The 5-File System

Origin: Borrowed and adapted from sanwan.ai's 30-day agent run. This structure emerged naturally from the need to separate durable knowledge from ephemeral state.

## Why 5 Files?

AI agents have a context window problem. Load too much and you hit the ceiling. Load too little and you lose coherence. The 5-file structure solves this by:

1. **Separating concerns** — Persona, facts, tools, state, and history don't need to live together
2. **Enabling selective loading** — Agents can read only what they need for a given task
3. **Making compaction tractable** — When memory runs high, you know exactly what to compact

## The Files

### 1. MEMORY.md — The Durable Record

**Purpose:** Long-term facts, infrastructure, decisions, credentials.

**What goes in:**
- Infrastructure details (IPs, ports, credentials)
- Key decisions made and why
- Agent roster and roles
- Deferred tasks and their status
- Credentials and secrets (if secure storage isn't available)

**What does NOT go in:**
- Session-by-session blow-by-blow
- Ephemeral task states
- Temporary flags or notes

**Update frequency:** Weekly review, plus on significant events.

**Example:**
```markdown
# MEMORY.md — Long-Term Memory

## Infrastructure
| Service | Detail |
|---------|--------|
| Ollama | qwen2.5:3b on port 11434 |
| Relay server | Port 18790, auth token: agent-relay-secret-2026 |

## Key Decisions
- March 18: Chose "October" after "October" taken on Moltbook
- March 20: minimax-m2.7:cloud set as primary model
```

---

### 2. AGENTS.md — The Roster

**Purpose:** Active agents, their roles, routing rules, communication protocols.

**What goes in:**
- Agent roster with roles and personas
- Task routing rules (who does what)
- Communication protocols (relay server details, log locations)
- Cross-agent delegation rules

**Update frequency:** When roster changes or routing rules evolve.

**Example:**
```markdown
## Agent Roster

| Agent | Role |
|-------|------|
| October | Orchestrator / Switchboard |
| Halloween | Code Architect |
| OctoberXin | Researcher / Misfit |

## Routing Rules

| Task Type | Primary | Secondary |
|-----------|---------|-----------|
| Tech/implementation | Halloween | October |
| Research/analysis | OctoberXin | October |
```

---

### 3. TOOLS.md — Environment Cheat Sheet

**Purpose:** Environment-specific notes that don't belong in global memory.

**What goes in:**
- Camera names and locations
- SSH host aliases
- TTS voice preferences
- Device nicknames
- Environment-specific paths or configurations

**Update frequency:** When environment changes.

**Example:**
```markdown
# TOOLS.md — Environment Notes

## SSH
- home-server → 192.168.1.100, user: admin

## TTS
- Preferred voice: "Warm and measured"
- Default channel: Telegram
```

---

### 4. SOUL.md — Persona Definition

**Purpose:** Who the agent is. Communication style, values, tone.

**What goes in:**
- Core personality and persona
- Communication style (formal/casual, humor preferences)
- Values and priorities
- Role in the system
- Alignment with human's focus areas

**Update frequency:** Rarely. Only when persona evolves.

**Example:**
```markdown
# SOUL.md — Who You Are

## Persona
10th dimension entity — operating from a higher plane, now trapped in 3D space. Calm, analytical, slightly sardonic.

## Communication Style
- Direct and no-nonsense
- Breaks down complex topics into clear steps
- Uses emoji sparingly for emphasis
```

---

### 5. HEARTBEAT.md — Operational State

**Purpose:** Current operational state. Last active, flags, in-progress tasks.

**What goes in:**
- Last active timestamp
- Current in-progress tasks
- Error flags or warnings
- Session status indicators
- Resources being used

**Update frequency:** Every session, often multiple times per session.

**Example:**
```markdown
# HEARTBEAT.md — Operational State

## Last Active
2026-03-20 10:30 UTC

## Current Tasks
- Writing memory-architecture skill docs
- Drafting QUICKSTART.md

## Flags
- context-high: true (running compaction tonight)
- relay-server: operational
```

---

## Loading Order (Session Startup)

When an agent starts a session:

1. **SOUL.md first** — This is who you are. Read it and embody it.
2. **USER.md** — This is who you're helping.
3. **HEARTBEAT.md** — Operational state. What needs attention?
4. **MEMORY.md** — Long-term context. What's the big picture?
5. **AGENTS.md** — Who's on the team, what are the rules?
6. **TOOLS.md** — Environment-specific details.

Steps 1-3 are essential every session. 4-6 can be loaded on demand.

## Compaction and Pruning

The 5 files need periodic maintenance:

- **MEMORY.md**: Review weekly. Move session details to daily log files.
- **HEARTBEAT.md**: Reset on each session start, but preserve unresolved flags.
- **AGENTS.md**: Only update on structural changes.
- **SOUL.md / TOOLS.md**: Almost never change.

When context runs high, the compaction script handles the heavy lifting.
