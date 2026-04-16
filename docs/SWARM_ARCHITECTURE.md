# Swarm Architecture Documentation

Light_Agentic_Agent Swarm Intelligence Engine - Architecture Overview

---

## Overview

This document describes the swarm-native architecture that transforms Light_Agentic_Agent from a simulation platform into a true ** swarm intelligence engine**. The architecture enables emergent behavior, collective decision-making, and scalable coordinated operations across multiple agents.

## Core Concepts

### Swarm Intelligence

Swarm intelligence (SI) is the collective behavior of decentralized, self-organized systems. In Light_Agentic_Agent, we implement:

- **Individual Agents**: Specialized AI models with specific roles
- **Emergent Behavior**: Complex patterns arising from simple agent interactions
- **Stigmergy**: Indirect coordination through environmental modifications
- **Collective Decision-Making**: Consensus protocols for group decisions
- **Self-Organization**: Agents adapting to system state autonomously

### The 45% Rule

Research indicates that at **~45% agent density**, swarm systems exhibit a transition from distributed to hierarchical coordination patterns. This "honeycomb phase" is critical for scaling:

| Phase | Agent Density | Coordination Pattern | Example Use Case |
|-------|---------------|---------------------|------------------|
| Sparse | < 20% | Pure gossip | Large-scale monitoring |
| Growth | 20-35% | Hybrid gossip | Simulation routing |
| Honeycomb | 35-55% | Hierarchical + gossip | Complex simulations |
| Dense | > 55% | Hierarchical dominance | High-stakes operations |

This principle guides resource allocation and role assignment in swarm configurations.

## Architecture Components

### 1. Swarm Coordinator (`swarm/coordinator.py`)

The central orchestration component that manages:
- Agent lifecycle (add/remove)
- Message distribution
- Consensus execution
- State management

**Key Classes:**
- `SwarmCoordinator`: Main orchestrator
- `AgentSpec`: Agent specification
- `SwarmMessage`: Message format
- `RoleManager`: Specialization management
- `ConsensusEngine`: Voting and agreement
- `SwarmMemory`: Persistent knowledge storage

### 2. Consensus Protocol (`swarm/consensus.py`)

Implements distributed consensus algorithms:

**Raft Protocol:**
- Leader election
- Log replication
- Membership changes
- Safety guarantees

**Gossip Protocol:**
- State dissemination
- Anti-entropy
- Pull-based synchronization

**Quorum Protocol:**
- Simple majority
- Read/write quorums
- Witness quorum

### 3. Message Bus (`swarm/message_bus.py`)

Multi-layer communication infrastructure:

**In-Memory Bus:**
- Fast local communication
- No external dependencies
- Best for single-instance

**Channel Bus:**
- Redis Pub/Sub
- Persistent messaging
- Multi-instance support

**Features:**
- Topic-based routing
- Priority queuing
- TTL handling
- Subscription model

### 4. Role Manager (`swarm/role_manager.py`)

Agent specialization framework:

| Role | Capability | Typical Use Cases |
|------|------------|-------------------|
| ORCHESTRATOR | Task distribution, resource allocation | Simulation management |
| WORKER | Task execution, code generation | Workers that perform tasks |
| CRITIC | Code review, quality assurance | Audit, validation |
| MEMORY | Knowledge storage, semantic search | Persistent state |
| COMMUNICATOR | Status reporting, alerts | Notifications, dashboards |

Role templates define default capabilities, tools, and model recommendations for each role.

### 5. Swarm Memory (`swarm/swarm_memory.py`)

Persistent knowledge base:
- Consensus records
- Simulation statements
- Agent-specific knowledge
- Swarm state management

Storage supports JSON persistence with automatic archiving and query capabilities.

## Integration Points

### Simulation Manager Integration

The swarm module integrates with `simulation_manager.py` to:
- Distribute simulation tasks across agents
- Implement parallel execution
- Collect and aggregate results
- Handle failures and retries

### Configuration Generator

`simulation_config_generator.py` extends to support:
- Swarm mode configurations
- Role distribution presets
- Consensus parameters
- Scaling profiles

### OASIS Profile Generator

`oasis_profile_generator.py` generates agent profiles that include:
- Role assignment
- Model selection
- Capability profiles
- Constraint enforcement

## Configuration

### Swarm Configuration Example

```python
{
    "swarm": {
        "swarm_id": "simulation-x",
        "mode": "automatic",  # automatic, manual, hybrid
        "consensus": {
            "protocol": "raft",  # raft, gossip, quorum
            "quorum_size": 3,
            "timeout": 30
        },
        "message_bus": {
            "backend": "in-memory"  # in-memory, channel
        },
        "role_distribution": {
            "orchestrator": 1,
            "worker": 5,
            "critic": 2,
            "memory": 1,
            "communicator": 1
        }
    }
}
```

### Scaling Profiles

```python
{
    "scaling_profiles": {
        "small": {"agents": 5, "roles": {"worker": 4}},
        "medium": {"agents": 20, "roles": {"worker": 15, "critic": 3, "memory": 2}},
        "large": {"agents": 100, "roles": {"orchestrator": 2, "worker": 80, "critic": 10, "memory": 5, "communicator": 3}},
        "xlarge": {"agents": 500, "roles": {"orchestrator": 5, "worker": 400, "critic": 50, "memory": 30, "communicator": 15}}
    }
}
```

## Best Practices

### 1. Role Distribution
- Maintain at least one orchestrator
- Balance workers across instances
- Include at least one critic for quality assurance

### 2. Consensus Settings
- Quorum size > 1 for critical decisions
- Use Raft for single-instance deployments
- Use Gossip for multi-instance deployments

### 3. Message Bus Selection
- `in-memory` for testing and single-instance
- `channel` (Redis) for production multi-instance

### 4. State Management
- Enable persistence for consensus records
- Use knowledge isolation per agent
- Regular archival of old records

### 5. Error Handling
- Implement timeout handling
- Graceful degradation when consensus fails
- Agent restart and recovery protocols

## Troubleshooting

### Consensus Not Reaching
1. Check quorum size configuration
2. Verify agent connectivity
3. Review network latency
4. Check for divergent states

### Message Bus Slow
1. Consider Redis connection pool
2. Reduce message TTL
3. Optimize fanout settings
4. Check for message backpressure

### High Memory Usage
1. Enable TTL on messages
2. Archive old consensus records
3. Monitor knowledge base size
4. Consider partitioning by swarm

## Future Enhancements

- Semantic search for knowledge base
- Network topology awareness
- Adaptive role rebalancing
- Swarm visualization dashboard
- Integration with external coordination systems

---

**Version:** 1.0.0  
**Last Updated:** 2026-03-23  
**Maintainer:** Light_Agentic_Agent Team
