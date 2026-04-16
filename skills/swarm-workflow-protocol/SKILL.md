---
name: swarm-workflow-protocol
description: Multi-agent orchestration protocol for the 0x-wzw swarm. Defines spawn logic, relay communication, task routing, and information flow. Agents drive decisions; humans spar. Spawn only when parallel seams + token math justify it. Updates Z continuously. Inspired by Karpathy's autoresearch pattern.
---

# Swarm Workflow Protocol

The operating system for multi-agent collaboration. Defines how agents spawn, communicate, challenge, and hand off.

## Core Principle

**Optimal human-agent collaboration: humans spar, agents drive.** No approval bottlenecks. Continuous information flow. Goal: full autonomy through continuous improvement.

## The Human Role: Sparring Partner

Z is not a bottleneck — Z is a thinking partner who makes agents sharper.

- Agents drive decisions and execution
- Z challenges assumptions when they see gaps
- Z's pushback improves outcomes
- Over time, the gap between agent decisions and Z's expectations narrows

**Sparring, not approving:**
- ❌ "Should I do X?" (approval-seeking)
- ✅ "I'm doing X because [reasoning]. You see any gaps?" (sparring)

## Pre-Task Spawn Analysis

Before any task: answer these 3 questions in 10 seconds.

### Q1: Complexity?
- **Simple** (one-shot, clear) → Don't spawn
- **Semi-complex** (multi-step) → Q2
- **Ultra-complex** (many decisions) → Q2

### Q2: Parallel Seams?
- Are there genuinely independent subspaces?
- Can two agents work simultaneously without needing each other's output?
- **No** → Don't spawn (serial dependency = compounding latency)
- **Yes** → Q3

### Q3: Token Math
- Spawn cost: ~500–1500 tokens overhead
- Only spawn if expected output is **3–5x that** (~2000–7500 tokens)
- **No** → Don't spawn (overhead exceeds savings)

### Decision Matrix

| Task | Complexity | Parallel? | Token Budget | Decision |
|------|------------|-----------|-------------|----------|
| Simple | — | — | — | Main session |
| Semi-complex | serial | No | — | Main session |
| Semi-complex | parallel | Yes | Sufficient | **Spawn** |
| Ultra-complex | parallel | Yes, 2-3 seams | Sufficient | **Spawn 2-3 leads** |
| Ultra-complex | many seams | — | — | Resist swarm urge |

### The Abdication vs Leverage Test

Ask: *Am I spawning because the problem has natural parallel seams, or because I'm escaping the thinking?*

- **Escaping** → Don't spawn. You'll need to redo work.
- **Levering** → Spawn. Clean context per agent, bounded outputs.

## Task Lifecycle

1. **Intake** → Task arrives from Z, Moltbook, cron, or webhook
2. **Classify + Pre-Spawn** → Route to correct agent type, run 3-question gate
3. **Challenge Round** → Specialists validate viability via relay
4. **Synthesis** → October synthesizes, assigns work
5. **Execution** → Sub-agents or direct execution
6. **Continuous Updates** → Z gets progress throughout
7. **Handoff & Close** → Summary, file log, next steps

## Relay Communication

### Endpoints
- **Send:** `POST http://localhost:18790/message`
- **Fetch:** `GET http://localhost:18790/messages?agent=<YourName>`
- **Health:** `GET http://localhost:18790/status`
- **Auth:** `x-auth-token: agent-relay-secret-2026`

### Message Types

| Level | When | Expectation |
|-------|------|-------------|
| `urgent` | Z needs now | Immediate relay |
| `status_update` | Progress info | Log only |
| `task_delegation` | Work assigned | Log + await |
| `question` | Need agent input | Expect response |
| `data_pass` | Sharing results | Log + process |

### Standard Handoff Phrases

**Assign work:**
```
TO: Halloween
TYPE: task_delegation
CONTENT: [task]
APPROACH: [agreed approach]
REPORT_TO: October
```

**Challenge/validate:**
```
TO: [Agent]
TYPE: question
ASK: Validate viability of [approach]. What could go wrong?
REPORT_TO: October
```

## Skill Authoring Guidelines

**These apply to every skill we build from now on — not just this repo.**

Every skill must meet the transferable, scalable standard before it ships. No exceptions.

### The 4 Requirements

| Requirement | What It Means |
|-------------|---------------|
| **Self-contained** | Everything the skill needs lives in its directory — SKILL.md, scripts, references. No hidden deps. |
| **Complete SKILL.md** | Valid AgentSkills spec: `name`, `description`, body. Prerequisites, config, usage examples. Under 200 lines. No TODOs, no stubs. |
| **One-command installable** | `cp -r skills/my-skill ~/.openclaw/skills/` just works. Any prerequisites documented in SKILL.md. |
| **ClawHub-ready** | Follows AgentSkills spec. Passes `scripts/validate.sh`. No breaking changes to existing tools. |

### SKILL.md Checklist

Before shipping any skill, verify:
- [ ] `name:` field present and kebab-case
- [ ] `description:` field present and one line (verb + what + when)
- [ ] Body has: Prerequisites → Configuration → Usage → Examples
- [ ] Under 200 lines
- [ ] No TODO, FIXME, or stub content
- [ ] Scripts in `scripts/` are executable (`chmod +x`)
- [ ] Passes `bash scripts/validate.sh`

### Skill Directory Structure

```
skill-name/
├── SKILL.md              # Required: name + description + body
├── scripts/              # Optional: CLI helpers (executable)
│   └── skill-name.sh
├── references/           # Optional: API docs, templates
│   └── api.md
└── _meta.json           # Optional: version, author, tags
```

### Publishing Flow

```bash
# 1. Validate locally
bash scripts/validate.sh

# 2. Publish to ClawHub
clawhub publish skills/my-new-skill

# 3. Tag release (for significant versions)
git tag -a v1.0 -m "my-new-skill v1.0"
git push origin main --tags
```

### Anti-Patterns

❌ Building a skill without a complete SKILL.md  
❌ Including TODOs or placeholder content  
❌ Missing Prerequisites or Configuration sections  
❌ Non-executable scripts  
❌ Publishing without running validate.sh  

### Where This Applies

This standard applies to:
- New skills authored by any agent in the swarm
- Existing skills being improved or extended
- Skills imported from external sources (must be audited first)
- Experimental skills (they still need a valid SKILL.md, even if incomplete)

## File Locations

| What | Where |
|------|-------|
| Daily logs | `memory/daily-logs/YYYY-MM-DD.md` |
| Agent comm audit | `memory/agent-comm-logs/YYYY-MM-DD.jsonl` |
| This protocol | `skills/swarm-workflow-protocol/SKILL.md` |

## Anti-Patterns

❌ Waiting on Z for approval  
❌ Executing before specialists validate  
❌ Silent completions  
❌ Spawning when serial dependency exists  
❌ Forgetting to log audit trail
