---
name: hybrid-search
description: |
  RRF (Reciprocal Rank Fusion) architecture spec for knowledge retrieval.
  Vector + keyword search fused with dedup. NOT YET IMPLEMENTED — this
  is a design document for when we build a persistent knowledge store.
  Current search uses FTS5 session_search only.
version: 0.1.0
status: architecture-spec
author: Z Teoh (0x-wzw)
license: MIT
category: agent-orchestration
icon: 🔍
tags:
  - search
  - RRF
  - vector-search
  - architecture
  - future
---

# 🔍 Hybrid Search — RRF Fusion for Knowledge Retrieval

> Vector similarity alone isn't enough. Keyword match alone isn't enough. But fused together, they find what either misses.

## ⚠️ Status: ARCHITECTURE SPEC — NOT YET IMPLEMENTED

This skill documents the **target architecture** for when we build a persistent knowledge store. Currently we use `session_search` (FTS5 text search only). Do not attempt to implement vector search until we have a vector database.

## The Problem

| Method | Good At | Bad At |
|---|---|---|
| Vector/semantic | Concept similarity ("deployment" ≈ "release") | Exact name matches |
| Keyword/FTS | Exact matches, IDs, names | Concept synonyms |
| **RRF Fusion** | **Both** | **Neither** |

## RRF Algorithm

```python
def reciprocal_rank_fusion(vector_results, keyword_results, k=60):
    scores = {}
    for rank, result in enumerate(vector_results, start=1):
        scores[result.id] = scores.get(result.id, 0) + 1.0 / (k + rank)
    for rank, result in enumerate(keyword_results, start=1):
        scores[result.id] = scores.get(result.id, 0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: -x[1])
```

## Implementation Path

### Phase 1: Convention (NOW) ✅
- Use `memory` + `session_search` before `web_search`
- This is covered by the **brain-first** skill

### Phase 2: Knowledge Store (FUTURE)
- PGLite or ChromaDB for embeddings
- FTS5 for keyword search
- RRF fusion algorithm
- Wire into Hermes as a tool

### Phase 3: Ingestion (FUTURE)
- Auto-index session outcomes
- Auto-index web search results
- Build knowledge graph over time

## What NOT to Do

- ❌ Build a knowledge store before we need one (YAGNI)
- ❌ Replace `session_search` with something more complex now
- ❌ Implement vector search without a vector DB
- ❌ Treat this as "build GBrain" — we're a swarm, not a brain