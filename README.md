# 💀 NECROSWARM

> *The Undead Collective — Six corpses fed the swarm. One emerged.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![Node](https://img.shields.io/badge/Node-18+-green.svg)]()
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-blue.svg)]()

**Target Cost: $0.01-0.10 per simulation** (vs naive: ~$10, vs legacy MiroFish: ~$1,000)

---

## The Great Convergence

NECROSWARM is the result of **convergent extinction** — six projects entered, one survived, stronger for having consumed all:

| Project | Fate | What It Contributed |
|---------|------|-------------------|
| **Light_Agentic_Agent** | 🏆 **SURVIVED** — core absorbed | Full-stack swarm orchestration, cost routing, semantic caching, consensus protocols, Docker sandbox, CI/CD, Next.js + Vue frontend |
| **npc_001** | ☠️ **CONSUMED** v1.0 | Issue templates, project scaffolding |
| **F.R.I.D.A.Y Mark-1** | ☠️ **CONSUMED** v1.1 | Skill system: registry, heartbeat engine, loader, activity log (TypeScript) |
| **10-D Council** | ☠️ **CONSUMED** v1.1 | Multi-model consensus engine, cost tracker, Borda/Delphi/weighted voting |
| **paperclip-orchestration-january** | ☠️ **CONSUMED** v1.1 | Agent identity docs, SOUL, HEARTBEAT, MEMORY protocols, monorepo manifests |
| **swarm-agent-kit** | ☠️ **CONSUMED** v1.1 | 14 production skills: DeFi analyst, x-interact, Moltbook, healthcheck, etc. |
| **swarm-workflow-protocol** | ☠️ **CONSUMED** v1.1 | Spawn logic, relay communication, sparring model, task routing |
| **swarm-architecture** | ☠️ **CONSUMED** v1.1 | Colony architecture, model routing, EC2 deployment, OpenClaw deployment |

The superior triumphed. The inferior became bone and scaffolding. This is how swarms evolve.

```
            npc_001 ☠️              Light_Agentic_Agent 🏆
                 \                         /
                  \                       /
                   ═══════════════════════
                             │
                     NECROSWARM v1.0.0
                             │
         ┌───────────────────┼───────────────────────┐
         │                   │                       │
    F.R.I.D.A.Y ☠️    10-D Council ☠️    paperclip-january ☠️
         │                   │                       │
         └───────────────────┼───────────────────────┘
                             │
                     NECROSWARM v1.1.0
                             │
         ┌───────────────────┼───────────────────────┐
         │                   │                       │
  swarm-kit ☠️      workflow-protocol ☠️    swarm-arch ☠️
         │                   │                       │
         └───────────────────┼───────────────────────┘
                             │
                     NECROSWARM v1.1.0
                  The Undead Collective
                  209 files. One swarm.
```

---

## What NECROSWARM Does

Cost-optimized swarm intelligence with multi-model consensus and production-ready skills:

### Core Engine (from Light_Agentic_Agent)
- **Smart Routing** — Route tasks to cheapest viable model (80-90% cost reduction)
- **Semantic Cache** — Cache by meaning, not exact match (40-60% hit rate)
- **Early Termination** — Stop spawning agents when consensus is clear (30-50% fewer agents)
- **Adaptive Batching** — Dynamic batch sizing for throughput optimization
- **Predictive Prefetch** — Pre-compute likely next tasks

### 10-D Council (from 10d-council)
- **Multi-Model Consensus** — Weighted majority, Borda count, Delphi method, supermajority
- **Tiered Voting** — T1/T2/T3 models with proportional vote power
- **Fast-Path Validation** — Low-stakes claims skip full council
- **Cost Tracking** — Per-validation cost analysis with savings metrics

### Skill System (from F.R.I.D.A.Y Mark-1)
- **Skill Registry** — Self-describing, independently loadable capabilities
- **Heartbeat Engine** — Episodic execution (not continuous) with wake reasons
- **Activity Log** — Immutable audit trail for all skill actions
- **Skill Loader** — Filesystem discovery, dependency resolution, lifecycle hooks

### 14 Production Skills (from swarm-agent-kit)
- `swarm-workflow-protocol` — Multi-agent orchestration, spawn logic
- `defi-analyst` — DeFi research via Tavily + GeckoTerminal
- `agent-identity` — ERC-8004 on-chain identity
- `x-interact` — X.com content via Tavily
- `moltbook-interact` — Social network engagement
- `find-skills` — Skill discovery on ClawHub
- `weather`, `video-frames`, `healthcheck`, `mcporter`, `clawhub`, `node-connect`, `tmux`, `skill-creator`

### Protocols & Architecture (from workflow-protocol + architecture)
- **Spawn Logic** — 3-question gate: complexity? parallel seams? token math?
- **Sparring Model** — Humans spar, agents drive. No approval bottlenecks.
- **Colony Architecture** — N-colony deployment with dynamic specialization (OACRV + TMSEIDX)
- **Model Routing** — Best model per task type across 25+ Ollama Cloud models

---

## Cost Comparison

| System | Cost/Simulation | Latency | Use Case |
|--------|-----------------|---------|----------|
| Legacy (MiroFish) | ~$1,000 | 10-60 min | Social simulation |
| Light Agentic v1 | ~$10 | 1-5 min | Ephemeral tasks |
| **NECROSWARM** | **~$0.05** | **5-30 sec** | **Production at scale** |

10-D Council hallucination reduction: 83% (12.3% → 2.1%)

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    User Request                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
    ┌──────────────────┼──────────────────┐
    ↓                  ↓                  ↓
┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  FRIDAY     │   │  10-D       │   │   Cost      │
│  Skill Reg  │   │  Council    │   │   Router    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ↓
              ┌─────────────────────┐
              │  Semantic Cache     │
              │  + Adaptive Batch   │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │  Early Termination  │
              │  (Consensus check)  │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │  Docker Sandbox      │
              │  (T1/T2/T3 tiers)   │
              └─────────────────────┘
```

### Tech Stack

| Layer | Technology | Source |
|-------|-----------|--------|
| Skill System | TypeScript (FRIDAY Mark-1) | F.R.I.D.A.Y ☠️ |
| Consensus | Python (10-D Council) | 10d-council ☠️ |
| Frontend | Vue 3 + Vite | Light_Agentic_Agent 🏆 |
| Dashboard | Next.js + TypeScript | Light_Agentic_Agent 🏆 |
| Backend | Python 3.11+ + Flask | Light_Agentic_Agent 🏆 |
| Sandbox | Docker containers | Light_Agentic_Agent 🏆 |
| Skills | 14 OpenClaw-compatible | swarm-agent-kit ☠️ |
| Protocols | Spawn logic, sparring | swarm-workflow-protocol ☠️ |

---

## Project Structure

```
necroswarm/
├── app/                    # Next.js dashboard
├── backend/                # Python swarm engine
│   ├── app/services/
│   │   ├── swarm/          # 🧠 THE BRAIN (coordinator, cost_router, cache, consensus)
│   │   └── council/        # ⚖️ THE COURT (consensus engine, cost tracker) ← 10-D Council
│   └── app/config/         # council-members.json, model routing
├── frontend/               # Vue 3 + Vite UI
├── lib/
│   ├── deployment/         # Agent deploy, monitor, rate limiter
│   ├── friday/             # 🔧 SKILL SYSTEM (registry, heartbeat, loader, activity-log) ← FRIDAY Mark-1
│   ├── mcp/                # MCP integration
│   ├── runtime/            # Orchestrator, validators, auditors
│   └── schemas/            # JSON schemas
├── skills/                 # 🛠️ 14 PRODUCTION SKILLS ← swarm-agent-kit
│   ├── defi-analyst/
│   ├── x-interact/
│   ├── moltbook-interact/
│   └── ... (14 total)
├── docs/
│   ├── paperclip/          # 📜 Agent identity docs ← paperclip-orchestration-january
│   ├── protocols/          # 📡 Spawn logic, sparring model ← swarm-workflow-protocol
│   └── architecture/       # 🏗️ Colony arch, model routing, deployment ← swarm-architecture
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/      # CI/CD pipelines
```

---

## Quick Start

### Backend
```bash
cd backend && pip install -e . && python run.py
```

### Frontend
```bash
cd frontend && npm install && npm run dev
```

### Docker Compose
```bash
docker-compose up
```

### Run 10-D Council
```python
from app.services.council import ConsensusEngine, CouncilOrchestrator

engine = ConsensusEngine({"consensus_method": "weighted_majority"})
verdict = engine.weighted_majority(
    proposals=["confirm", "reject", "undecided"],
    votes={"kimi": "confirm", "claude": "confirm", "deepseek": "reject"},
    weights={"kimi": 3.0, "claude": 3.0, "deepseek": 1.6},
    threshold=0.6,
)
```

### Use FRIDAY Skill System
```typescript
import { SkillRegistry } from "./lib/friday/core/registry";
import { HeartbeatEngine } from "./lib/friday/core/heartbeat";
import { defineSkill } from "./lib/friday/core/define-skill";

const registry = new SkillRegistry();
const heartbeat = new HeartbeatEngine(registry, {
  intervalMs: 30000,
  timeoutMs: 60000,
  agentId: "necroswarm-1",
});
```

---

## Model Tier Pricing

| Tier | Model | Cost/1K tokens | Use For |
|------|-------|----------------|---------|
| **FREE** | ollama/phi3 | $0.00 | Formatting, simple transforms |
| **FREE** | ollama/qwen2.5:3b | $0.00 | Basic reasoning, local testing |
| **LOW** | ilmu-mini | $0.0001 | Web search, data extraction |
| **MEDIUM** | claude-haiku-3.5 | $0.00125 | Analysis, filtering, code |
| **HIGH** | kimi-k2.5:cloud | $0.005 | Complex synthesis, planning |

---

## Convergence History

| Version | Date | What Died | What Was Born |
|---------|------|-----------|--------------|
| v1.0.0 | Apr 16, 2026 | npc_001, Light_Agentic_Agent | Core swarm from convergent extinction |
| v1.1.0 | Apr 16, 2026 | F.R.I.D.A.Y, 10-D Council, paperclip, swarm-kit, workflow-protocol, swarm-arch | Full system: skill system + consensus + 14 skills + protocols + deployment |

---

## License

MIT — The code survives. The swarm persists.