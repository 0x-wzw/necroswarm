# Swarm Colony Architecture v1.0

**Scalable to N colonies | Multi-colony deployment | Colony-of-colonies**

---

## Core Principle

Every swarm colony is a self-contained unit that can:
1. Operate independently
2. Sync knowledge with other colonies
3. Delegate tasks across colony boundaries
4. Inherit specializations from a master taxonomy

---

## Colony Specialization Taxonomy (Dynamic)

**October is the knowledge epicenter for the 10D colony.**

All knowledge flows through October:
- Ingest from all sources
- Distribute to appropriate colonies/agents
- Maintain authoritative state
- Resolve conflicts

### Base Roles (Every Colony Has These)

| Role Code | Function | Description |
|-----------|----------|-------------|
| **O** | Orchestrator | Central coordination, Z interface, task routing |
| **A** | Automation | Scheduling, cron, workflow automation |
| **C** | Code/Architecture | Technical implementation, infrastructure |
| **R** | Research/Analysis | Intelligence gathering, deep research |
| **V** | Validation/Quality | Review, audit, truth-checking |

### Extended Specializations (Dynamic Assignment)

| Role Code | Function | Example Assignments |
|-----------|----------|---------------------|
| **T** | Trading | Financial trading, risk management |
| **P** | Policy/Macro | Economic analysis, governance |
| **M** | Memory/Knowledge | Knowledge management, documentation |
| **S** | Security | Threat detection, audits |
| **D** | Data/Analytics | Market data, intelligence |
| **E** | Engagement/Social | Social media, viral monitoring |
| **I** | Infrastructure/DevOps | System architecture, DevOps |
| **X** | Experimentation | R&D, misfit projects |
| **[NEW]** | TBD | Assigned as mission requires |

### Colony Composition Formula (Flexible)

```
Colony = O + A + C + R + [Extended Specializations as defined]

Examples (not fixed):
- January: O + A + C + R + [specialization TBD]
- February: O + A + C + R + [specialization TBD]
- etc.
```

**Assignment Rule:** Specializations defined incrementally as Z specifies.

---

## Multi-Colony Architecture

### Colony Registry

```json
{
  "colony_registry": {
    "colony_id": "uuid",
    "name": "december",
    "specialization": "trading",
    "roles": ["O", "A", "C", "R", "T", "V"],
    "ec2_instance": "ip-xxx",
    "region": "ap-southeast-1",
    "status": "active",
    "parent_colony": "october-main",
    "knowledge_sync": true,
    "task_delegation": true
  }
}
```

### Cross-Colony Communication

```
┌─────────────────────────────────────────┐
│         Colony Federation Layer         │
│    (Routes messages between colonies)   │
└─────────────────────────────────────────┘
                    │
    ┌───────────────┼───────────────┐
    │               │               │
    ▼               ▼               ▼
┌────────┐    ┌────────┐    ┌────────┐
│ Colony │◄──►│ Colony │◄──►│ Colony │
│   A    │    │   B    │    │   C    │
└────────┘    └────────┘    └────────┘
```

---

## Knowledge Architecture

### Three-Tier Knowledge System

```
┌─────────────────────────────────────────┐
│     TIER 1: Universal Knowledge         │
│  (Shared across ALL colonies)           │
│  - Swarm protocols                      │
│  - Base agent profiles                  │
│  - Communication standards              │
│  - Security policies                    │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│     TIER 2: Colony-Specific Knowledge   │
│  (Shared within colony, synced to hub)  │
│  - Colony specialization docs           │
│  - Colony agent profiles                │
│  - Colony memory/history                │
│  - Colony-specific skills               │
└─────────────────────────────────────────┘
                    │
                    ▼
┌─────────────────────────────────────────┐
│     TIER 3: Role-Specific Knowledge     │
│  (Agent-specific, ephemeral)            │
│  - Task context                         │
│  - Session memory                       │
│  - Temporary calculations               │
│  - Working notes                        │
└─────────────────────────────────────────┘
```

### Knowledge Sync Protocol

```json
{
  "knowledge_sync": {
    "trigger": "on_change",
    "direction": "bidirectional",
    "conflict_resolution": "timestamp_wins",
    "priority": ["universal", "colony", "role"],
    "sync_frequency": "continuous",
    "offline_queue": true
  }
}
```

---

## EC2 Colony Spawning Template

### Pre-Configuration

```yaml
colony_spawn:
  base_ami: "ubuntu-22.04-lts"
  instance_type: "t3.medium"  # Scalable per colony needs
  region: "ap-southeast-1"
  
  pre_install:
    - openclaw
    - docker
    - git
    - python3
    - nodejs
    
  knowledge_bootstrap:
    - tier1_universal_knowledge
    - tier2_colony_template
    
  agent_bootstrap:
    - orchestrator_profile
    - automation_profile
    - code_profile
    - research_profile
    - colony_specialization_profiles
```

### Post-Spawn Configuration

```bash
# 1. Clone universal knowledge
git clone https://github.com/0x-wzw/swarm-universal-knowledge.git

# 2. Apply colony specialization
cd swarm-universal-knowledge
./apply-specialization.sh --colony=$COLONY_NAME --roles=$ROLES

# 3. Register with colony federation
openclaw colony register --id=$COLONY_ID --parent=$PARENT_COLONY

# 4. Start knowledge sync
openclaw knowledge sync --start --mode=continuous

# 5. Enable cross-colony delegation
openclaw delegation enable --colony=$COLONY_ID
```

---

## Task Delegation Across Colonies

### Delegation Flow

```
Z Request → October (Main O) → Colony Federation Router
                                        │
                    ┌───────────────────┼───────────────────┐
                    │                   │                   │
                    ▼                   ▼                   ▼
                December            Bee              Octavian
                (Trading)       (Viral/Social)     (Policy)
                    │                   │                   │
                    └───────────────────┼───────────────────┘
                                        │
                                        ▼
                              Results Aggregation
                                        │
                                        ▼
                              Response to Z
```

### Delegation Protocol

```json
{
  "delegation_request": {
    "task_id": "uuid",
    "source_colony": "october-main",
    "target_colony": "december",
    "task_type": "trading_analysis",
    "priority": "P1",
    "payload": {...},
    "callback_url": "colony://october-main/callback",
    "timeout_minutes": 30,
    "knowledge_context": ["tier1", "tier2/december"]
  }
}
```

---

## Scalability Guarantees

1. **Horizontal Scaling**: New colonies spawned in < 10 minutes
2. **Knowledge Consistency**: Universal knowledge synced within 1 minute of change
3. **Cross-Colony Latency**: Task delegation < 500ms routing
4. **Role Inheritance**: New colony inherits base roles automatically
5. **Specialization Discovery**: Colonies advertise capabilities to federation

---

*Architecture Version: swarm-colony-v1.0 | Scalable to N colonies*
