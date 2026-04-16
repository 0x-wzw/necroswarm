# 💀 NECROSWARM

> *The Undead Collective — From the corpses of two agents, one swarm emerged.*

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)]()
[![Node](https://img.shields.io/badge/Node-18+-green.svg)]()

**Target Cost: $0.01-0.10 per simulation** (vs naive: ~$10, vs legacy MiroFish: ~$1,000)

---

## The Convergence

NECROSWARM is the result of **convergent extinction** — two projects entered, one survived, stronger for having consumed the other:

| Project | Fate | What It Contributed |
|---------|------|-------------------|
| **Light_Agentic_Agent** | 🏆 **SURVIVED** — core absorbed | Full-stack swarm orchestration, cost routing, semantic caching, consensus protocols, Docker sandbox, CI/CD, Next.js + Vue frontend |
| **npc_001** | ☠️ **CONSUMED** — skeleton harvested | Issue templates, project scaffolding, the hollow structure that became the frame |

The superior triumphed. The inferior became bone and scaffolding. This is how swarms evolve.

---

## What NECROSWARM Does

Cost-optimized swarm intelligence for production-scale agent coordination:

- **Smart Routing** — Route tasks to cheapest viable model (80-90% cost reduction)
- **Semantic Cache** — Cache by meaning, not exact match (40-60% hit rate)
- **Early Termination** — Stop spawning agents when consensus is clear (30-50% fewer agents)
- **Adaptive Batching** — Dynamic batch sizing for throughput optimization
- **Predictive Prefetch** — Pre-compute likely next tasks
- **Consensus Protocols** — Raft, Gossip, and Quorum-based distributed decision-making
- **Docker Sandbox** — Isolated agent execution environments
- **Swarm Memory** — Cross-simulation persistent knowledge base

### Cost Comparison

| System | Cost/Simulation | Latency | Use Case |
|--------|-----------------|---------|----------|
| Legacy (MiroFish) | ~$1,000 | 10-60 min | Social simulation |
| Light Agentic v1 | ~$10 | 1-5 min | Ephemeral tasks |
| **NECROSWARM** | **~$0.05** | **5-30 sec** | **Production tasks at scale** |

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
│   Semantic  │   │  Predictive │   │   Cost      │
│    Cache    │   │  Prefetch   │   │   Router    │
└──────┬──────┘   └──────┬──────┘   └──────┬──────┘
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ↓
              ┌─────────────────────┐
              │  Adaptive Batcher  │
              │   (Dynamic sizing) │
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │   Early Termination │
              │   (Consensus check)│
              └──────────┬──────────┘
                         ↓
              ┌─────────────────────┐
              │   Docker Sandbox    │
              │   (T1/T2/T3 tiers)  │
              └─────────────────────┘
```

### Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vue 3 + Vite |
| Dashboard | Next.js + TypeScript |
| Backend | Python 3.11+ + Flask |
| Consensus | Raft / Gossip / Quorum |
| Sandbox | Docker containers |
| LLM | OpenAI + Ollama (local) |
| Memory | Zep Cloud + Swarm Memory |
| CI/CD | GitHub Actions |

---

## Quick Start

### Backend

```bash
cd backend
pip install -e .
python run.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

```bash
docker-compose up
```

### Python API

```python
from app.services.swarm import CostOptimizedSwarmCoordinator

coordinator = CostOptimizedSwarmCoordinator(
    swarm_id="necroswarm",
    message_bus=InMemoryMessageBus(),
    role_manager=RoleManager(...),
    consensus_engine=ConsensusEngine(...),
    enable_docker=True,
    config=CostOptimizedConfig(
        enable_semantic_cache=True,
        enable_early_termination=True,
        enable_adaptive_batching=True,
    )
)

# Single optimized task
result = await coordinator.run_ephemeral_task_optimized(
    task="Summarize this financial report",
    role=AgentRole.ANALYST
)

# Batch processing
results = await coordinator.batch_execute(
    tasks=["Analyze Q1", "Analyze Q2", "Analyze Q3"],
    role=AgentRole.ANALYST
)

# Cost report
report = coordinator.get_optimization_report()
print(f"Total savings: ${report['metrics']['total_savings_usd']}")
```

---

## Project Structure

```
necroswarm/
├── app/                    # Next.js dashboard
│   ├── api/               # API routes (deploy, monitor, run)
│   ├── cicd/              # CI/CD dashboard page
│   └── layout.tsx         # Root layout
├── backend/               # Python swarm engine
│   ├── app/
│   │   ├── api/           # REST endpoints (graph, report, simulation)
│   │   ├── models/        # Data models (project, task)
│   │   ├── services/      # Core services
│   │   │   ├── swarm/     # 🧠 THE BRAIN
│   │   │   │   ├── coordinator.py        # v1 coordinator
│   │   │   │   ├── coordinator_v2.py      # Cost-optimized v2
│   │   │   │   ├── cost_router.py         # Smart model routing
│   │   │   │   ├── batching_cache.py     # Semantic cache + batching
│   │   │   │   ├── consensus.py           # Raft/Gossip/Quorum
│   │   │   │   ├── docker_sandbox.py      # Container isolation
│   │   │   │   ├── message_bus.py         # Inter-agent comms
│   │   │   │   ├── role_manager.py        # Agent specialization
│   │   │   │   └── swarm_memory.py        # Persistent knowledge
│   │   │   └── ...        # Report, simulation, ontology services
│   │   └── utils/         # LLM client, file parser, retry logic
│   └── scripts/           # Run scripts (parallel, reddit, twitter)
├── frontend/              # Vue 3 + Vite UI
│   └── src/
│       ├── views/         # Main, Simulation, Report, Interaction
│       └── components/    # Graph, Step, History panels
├── lib/                   # TypeScript libraries
│   ├── deployment/        # Agent deploy, monitor, rate limiter
│   ├── mcp/               # MCP integration (auth, client, registry)
│   ├── runtime/           # Orchestrator, validators, auditors
│   └── schemas/           # JSON schemas for audit, deploy, spec
├── docs/
│   ├── SCALING.md
│   └── SWARM_ARCHITECTURE.md
├── Dockerfile
├── docker-compose.yml
└── .github/workflows/     # CI/CD pipelines
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

## Performance Targets

| Metric | Target | Status |
|--------|--------|--------|
| Cost per 100 tasks | <$0.05 | ✅ Achieved |
| Cache hit rate | >60% | 🔄 Tuning |
| Early term rate | >40% | 🔄 Tuning |
| P99 latency | <5s | ✅ Achieved |
| Throughput | >100 req/s | 🔄 Scaling |

---

## Ancestry

```
npc_001 (☠️ consumed)     Light_Agentic_Agent (🏆 absorbed)
        \                              /
         \                            /
          ══════════════════════════
                    │
              💀 NECROSWARM
         The Undead Collective v1.0.0
```

---

## License

MIT — The code survives. The swarm persists.