# Swarm Delegation — FRIDAY Mark-1 Module

## Overview
Part of the F.R.I.D.A.Y. skill architecture. Handles multi-agent spawning decisions, context management, and token optimization for swarm orchestration.

## Core Question
Should I spawn a sub-agent, or handle this in the current context?

## Decision Gate (answer all 3)

### Q1: Complexity
| Level | Indicators | Decision |
|-------|-----------|----------|
| Simple | One-shot, clear answer, no dependencies | Main session |
| Semi-complex | Multi-step, some dependencies | Q2 |
| Ultra-complex | Many decision points, high interdependence | Q2 |

### Q2: Parallel Seams?
- Are there independent problem subspaces?
- Can agents work simultaneously without waiting for each other?
- **If no** → Don't spawn. Serial work stays in one context.
- **If yes** → Q3

### Q3: Token Math
- Spawn cost: ~500-1500 tokens overhead
- Only spawn if output will be 3-5x that (~2000-7500 tokens)
- **If math fails** → Don't spawn

## Spawn Decision Matrix
| Task | Parallel? | Tokens? | → |
|-------|----------|---------|---|
| Simple | — | — | Main session |
| Semi/serial | No | — | Main session |
| Semi/parallel | Yes | Sufficient | Spawn |
| Ultra (2-3 seams) | Yes | Sufficient | Spawn 2-3 |
| Ultra (many) | Yes | — | Resist — fragmentation risk |

## The Abdication Test
Am I spawning to escape the problem, or because the problem has natural parallel seams?

- **Escaping** → Don't spawn. Re-do the thinking.
- **Delegating** → Spawn. Clean bounded contexts.

## Nuclear Warning Signs
- Task keeps growing mid-execution → misclassified at intake
- Sub-agents keep needing each other's output → was serial
- Outputs don't synthesize → seams weren't independent
- Context compounds despite spawning → wrong agent granularity

**When you see these:** Pause. Re-classify. Stop spawning.

## Integration
Part of F.R.I.D.A.Y. Mark-1 skill system.
