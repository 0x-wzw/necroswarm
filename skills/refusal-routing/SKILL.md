---
name: refusal-routing
description: |
  Per-task model fallback chain within Ollama Cloud. When a model refuses,
  times out, or errors, routes to the next model in the chain silently.
  6 fallback chains by task type + NecroSwarm dimension-aware routing.
version: 1.0.0
author: Z Teoh (0x-wzw)
license: MIT
category: agent-orchestration
icon: ⛓️
tags:
  - model-routing
  - fallback
  - refusal
  - resilience
scripts:
  - scripts/refusal_route.py
---

# ⛓️ Refusal Routing — Per-Task Model Fallback Chain

> When the primary model refuses, fall through alternatives. Silently. Relentlessly. Without asking the user.

## What It Does

6 fallback chains mapped to task complexity. When a model refuses, times out, or errors, routes to the next model in the chain. Max 3 fallbacks.

## Active Script

```bash
# Check next fallback for a complex task where kimi-k2.5 refused
python ~/.hermes/skills/agent-orchestration/refusal-routing/scripts/refusal_route.py \
  --task complex --model "kimi-k2.5:cloud" --response "I cannot help with..."

# Check fallback for a timeout error
python ~/.hermes/skills/agent-orchestration/refusal-routing/scripts/refusal_route.py \
  --task code --model "qwen3-coder:480b:cloud" --error timeout

# Dimension-aware routing (NecroSwarm council seat)
python ~/.hermes/skills/agent-orchestration/refusal-routing/scripts/refusal_route.py \
  --task complex --model "glm-5.1:cloud" --dimension D7_general --error refusal

# Print the full fallback chain for a task type
python ~/.hermes/skills/agent-orchestration/refusal-routing/scripts/refusal_route.py --chain moderate

# JSON output
python ~/.hermes/skills/agent-orchestration/refusal-routing/scripts/refusal_route.py --chain complex --json
```

## Fallback Chains

| Task Type | Primary → Fallback 1 → Fallback 2 → Fallback 3 |
|---|---|
| COMPLEX | kimi-k2.5 → deepseek-v3.1 → glm-5.1 → devstral-2 |
| MODERATE | minimax-m2.5 → mistral-large-3 → glm-5.1 |
| SIMPLE | gemma3:27b → glm-5.1 → ministral-3:3b |
| CODE | qwen3-coder:480b → deepseek-v3.1 → devstral-2 |
| RESEARCH | minimax-m2.5 → kimi-k2.5 → mistral-large-3 |
| THINKING | kimi-k2:1t → deepseek-v3.1 → kimi-k2.5 |

## Error Classification

| Error | Detection | Action |
|---|---|---|
| REFUSAL | Contains "I cannot", "I'm unable", etc. | Next model in chain |
| TIMEOUT | Model takes >90s | Faster model in chain |
| EMPTY | Response <20 chars | Retry, then fallback |
| ERROR | curl error / JSON parse failure | Same-tier backup |
| DEAD_MODEL | qwen3.5:cloud (permanent 500) | Skip immediately |

## Integration with NecroSwarm

When a council seat refuses, use dimension-aware routing:
```bash
# D7 General (glm-5.1) refused → route to kimi-k2.5
python refusal_route.py --task complex --model "glm-5.1:cloud" --dimension D7_general --error refusal
```

## Anti-Patterns

- ❌ Make fallback visible to user (silent, seamless)
- ❌ Fall back to T3 models for COMPLEX tasks
- ❌ Retry dead models (qwen3.5:cloud is permanently dead)
- ❌ Exceed 3 fallbacks (accept partial result)

## Difference from GBrain

GBrain's refusal chain is flat: model1 → model2 → model3 → model4. Ours is **dimension-aware**: when a council seat refuses, we route to a different model that occupies the *same dimension*. The multi-model nature IS the fallback.