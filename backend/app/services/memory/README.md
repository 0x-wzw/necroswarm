# OpenClaw Memory Evolution

A self-improving memory system with access pattern tracking, time-based relevance decay, and relationship inference for AI agents.

## Overview

This system implements a background memory evolution process that makes agent memory self-improving through:

- **Access Pattern Tracking**: Monitors which memories are read/written and how often
- **Importance Decay**: Time-based relevance scoring (memories fade over time)
- **Relationship Inference**: Automatically links related memories
- **Memory Rewriting**: Updates entries based on usage patterns

## Installation

```bash
# Clone the repository
git clone https://github.com/0x-wzw/openclaw-memory-evolution.git
cd openclaw-memory-evolution

# No external dependencies required (Python 3.7+)
python -m test_evolution  # Run tests to verify
```

## Core Components

### 1. AccessPatternTracker

Monitors memory reads/writes to understand usage patterns:

```python
from evolution_agent import EvolutionAgent

agent = EvolutionAgent()
mem_id = agent.add_memory("Important fact about AI")

# Access is automatically tracked
agent.get_memory(mem_id, context="researching AI")

# Query frequently accessed memories
frequent = agent.access_tracker.get_frequently_accessed(threshold=5)
```

### 2. ImportanceDecay

Time-based relevance scoring with configurable half-life:

```python
from evolution_agent import ImportanceDecay

# Memories lose half their relevance every 30 days
decay = ImportanceDecay(half_life_days=30.0)
score = decay.calculate_score(memory)

# Check if memory should be archived
if decay.should_archive(memory, threshold=0.2):
    # Archive or remove low-relevance memory
    pass
```

### 3. RelationshipInference

Discovers connections between memories based on content similarity:

```python
# Automatically runs during evolution cycles
results = agent.run_evolution_cycle()
# Returns: relationships_inferred count

# Query for related memories
related = agent.relationships.find_related(memory, agent.memories)
```

### 4. MemoryRewriter

Suggests and applies memory updates:

```python
# Automatically triggers on frequently accessed memories with multiple contexts
rewrite_plan = agent.rewriter.suggest_rewrite(memory, related_memories)

# Actions: consolidate, enrich_tags, or none
```

## Usage

### Basic Usage

```python
from evolution_agent import EvolutionAgent

# Create agent
agent = EvolutionAgent(storage_path="memory_store.json")

# Add memories
mem1 = agent.add_memory("Python is great for ML", tags=["python", "ml"])
mem2 = agent.add_memory("PyTorch is a Python ML framework", tags=["python", "ml"])

# Access memories (tracks usage)
agent.get_memory(mem1, context="researching frameworks")

# Query memories
results = agent.query_memories("machine learning", limit=10)
for memory, score in results:
    print(f"{memory.content} (relevance: {score:.2f})")

# Run evolution cycle
stats = agent.run_evolution_cycle()
print(f"Processed {stats['memories_processed']} memories")
print(f"Inferred {stats['relationships_inferred']} relationships")
```

### Scheduler (Background Daemon)

Run evolution cycles automatically on a schedule:

```bash
# Run continuously with 60-minute intervals
python scheduler.py --interval 60 --log evolution.log

# Run once (for cron jobs)
python scheduler.py --once --status

# Check current status
python scheduler.py --status
```

#### Scheduler Options

| Option | Description | Default |
|--------|-------------|---------|
| `--storage` | Memory storage file path | `memory_store.json` |
| `--interval` | Minutes between cycles | `60` |
| `--heartbeat` | Heartbeat file for monitoring | `heartbeat.json` |
| `--once` | Run single cycle and exit | - |
| `--status` | Show current status | - |
| `--log` | Log to file | stdout |

#### HEARTBEAT.md Integration

The scheduler writes a heartbeat file for external monitoring:

```json
{
  "timestamp": 1711094400,
  "datetime": "2024-03-22T10:00:00",
  "status": "waiting",
  "run_count": 42,
  "next_run": 1711098000,
  "agent_stats": {
    "memory_count": 150
  }
}
```

### Programmatic Scheduler

```python
from scheduler import create_daemon_scheduler

scheduler = create_daemon_scheduler(
    storage_path="memory_store.json",
    interval_minutes=60.0,
    heartbeat_file="heartbeat.json"
)

# Run continuously
scheduler.start()

# Or run once
result = scheduler.start_once()

# Check status
status = scheduler.get_status()
```

## Configuration

### EvolutionAgent Parameters

```python
EvolutionAgent(
    storage_path="memory_store.json",      # Persistence file
    half_life_days=30.0,                    # Decay half-life
    similarity_threshold=0.6               # Relationship threshold
)
```

### Scheduler Parameters

```python
HeartbeatScheduler(
    agent=evolution_agent,
    interval_minutes=60.0,                  # Cycle interval
    heartbeat_file="heartbeat.json",       # Status file
    state_file="scheduler_state.json"       # Persistence
)
```

## Memory Rewriting Rules

The system automatically suggests rewrites when:

1. **Consolidation**: A memory is accessed 5+ times across 2+ different contexts AND has 3+ related memories
2. **Tag Enrichment**: A memory has related memories with tags it doesn't have
3. **Version Tracking**: Rewritten memories increment their version number

## Testing

```bash
# Run all unit tests
python test_evolution.py

# Run with verbose output
python -m unittest test_evolution -v
```

Tests cover:
- Access pattern tracking
- Importance decay calculations
- Relationship inference
- Memory rewriting
- Evolution cycles
- Scheduler functionality
- End-to-end integration

## API Reference

### EvolutionAgent

| Method | Description |
|--------|-------------|
| `add_memory(content, tags)` | Add new memory, returns memory ID |
| `get_memory(id, context)` | Retrieve memory and track access |
| `query_memories(query, limit)` | Search memories by relevance |
| `run_evolution_cycle()` | Execute one evolution cycle |
| `get_stats()` | Get comprehensive statistics |

### AccessPatternTracker

| Method | Description |
|--------|-------------|
| `record_access(id, operation, context)` | Log memory access |
| `record_sequence(ids)` | Log access sequence |
| `get_frequently_accessed(threshold)` | Get high-traffic memories |
| `get_coaccess_patterns()` | Find related access patterns |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EvolutionAgent                            │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌───────────────┐ │
│  │ AccessPattern   │  │ ImportanceDecay │  │ Relationship │ │
│  │    Tracker      │  │                 │  │  Inference   │ │
│  └─────────────────┘  └─────────────────┘  └───────────────┘ │
│                              │                                 │
│                    ┌─────────────────┐                        │
│                    │  MemoryRewriter │                        │
│                    └─────────────────┘                        │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────────────┐
                    │   MemoryStore     │
                    │   (JSON file)     │
                    └─────────────────┘
                              │
                    ┌─────────────────┐
                    │   Scheduler     │
                    │ (HeartbeatLoop) │
                    └─────────────────┘
```

## Integration with OpenClaw

This module is designed to integrate with the OpenClaw agent ecosystem:

1. **Memory Persistence**: JSON-based storage compatible with OpenClaw memory format
2. **Heartbeat Protocol**: Status reporting via heartbeat.json
3. **Background Processing**: Runs as daemon or scheduled job
4. **Stats Export**: Provides metrics for monitoring dashboards

## License

MIT License - See LICENSE file for details.

## Contributing

Contributions welcome. Please run tests before submitting:

```bash
python test_evolution.py
```
