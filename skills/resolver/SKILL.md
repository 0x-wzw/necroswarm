---
name: resolver
description: |
  Intent-to-skill dispatch engine. Pattern-matches user messages against
  a deterministic dispatch table to select the right skill. Integrates
  with NecroSwarm council deliberation for COMPLEX tasks.
version: 1.0.0
author: Z Teoh (0x-wzw)
license: MIT
category: agent-orchestration
icon: ⚫
tags:
  - dispatch
  - intent-resolution
  - skill-selection
  - resolver
capabilities:
  - intent-resolution
  - skill-dispatch
  - complexity-routing
scripts:
  - scripts/resolve.py
---

# ⚫ RESOLVER — Intent-to-Skill Dispatch

> The Dispatcher that turns intent into action. No ambiguity. No ad-hoc. Deterministic.

## What It Is

A single dispatch table that maps user intents to specific skills. Makes skill selection explicit, auditable, and deterministic. Integrates with NecroSwarm council deliberation for COMPLEX tasks.

## How It Works

```
User Message
     │
     ▼
┌─────────────┐
│  RESOLVER    │  ── Pattern-match against dispatch table
│  resolve.py │  ── Identify intents
└──────┬──────┘  ── Return matching skill(s)
       │
       ▼
┌─────────────┐
│  NecroSwarm  │  ── Pre-spawn analysis (3-question gate)
│  Council     │  ── Council deliberation if COMPLEX
└──────┬──────┘  ── Direct execution if SIMPLE
       │
       ▼
   Skill Execution
```

## Active Script

```bash
# Resolve an intent to matching skills
python ~/.hermes/skills/agent-orchestration/resolver/scripts/resolve.py "debug the login error"

# JSON output for programmatic use
python ~/.hermes/skills/agent-orchestration/resolver/scripts/resolve.py --json "deploy model to production"

# Exit 0 if match found, exit 1 if no match (triggers council fallback)
python ~/.hermes/skills/agent-orchestration/resolver/scripts/resolve.py "research transformers"
```

The script returns the matching skill, complexity rating, and model suggestion. No match → NecroSwarm council fallback.

## Dispatch Table (in resolve.py)

| Intent Pattern | Skill | Complexity |
|---|---|---|
| `code`, `implement`, `build` | subagent-driven-development | COMPLEX |
| `review`, `code review`, `PR` | requesting-code-review | MODERATE |
| `debug`, `error`, `failing` | systematic-debugging | MODERATE |
| `test`, `TDD` | test-driven-development | MODERATE |
| `plan`, `spec`, `requirements` | writing-plans | SIMPLE |
| `research`, `arxiv`, `papers` | arxiv | SIMPLE |
| `spawn`, `council`, `deliberate` | necroswarm | COMPLEX |
| `github`, `create repo`, `PR` | github-repo-management | SIMPLE |
| `fine-tune`, `LoRA`, `train` | axolotl | COMPLEX |
| `serve LLM`, `vLLM` | serving-llms-vllm | COMPLEX |
| ... | ... | ... |

Full table in `scripts/resolve.py` — 35+ intent patterns.

## Complexity → Model Routing

| Complexity | Model |
|---|---|
| TRIVIAL | ministral-3:3b:cloud |
| SIMPLE | gemma3:27b:cloud |
| MODERATE | minimax-m2.5:cloud |
| COMPLEX | kimi-k2.5:cloud |

## Anti-Patterns

- ❌ Routing to council for TRIVIAL tasks (waste of tokens)
- ❌ Bypassing RESOLVER and "just knowing" which skill to use
- ❌ Adding overlapping entries to the dispatch table
- ❌ Using RESOLVER for model routing (that's config.yaml's job)

## Difference from GBrain

GBrain's RESOLVER is a flat markdown file that dispatches `query` → tool. Ours is an **executable dispatch engine** with a script that feeds into a deliberation engine. GBrain resolves; we resolve, then *deliberate*.