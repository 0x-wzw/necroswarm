# Model Routing (Ollama Cloud — April 2026)

**All agents use Ollama Cloud models via Pro subscription.**

> **Updated:** April 4, 2026 — Added new 2026 releases, provider diversity analysis, best-in-class recommendations

---

## Latest Cloud Models (As of April 2026)

### Cloud-Enabled Models Available

| Model | Size | Type | Best For | Status |
|-------|------|------|----------|--------|
| **qwen3-coder** | 30b, 480b | Coding | Agentic coding, tool use | ⭐ Primary |
| **qwen3-coder-next** | 80b | Coding (Next-Gen) | Latest optimized coding | 🆕 New (1M+ pulls) |
| **devstral-2** | 123b | Coding | Codebase exploration, multi-file edit | ✅ Active |
| **devstral-small-2** | 24b | Coding | Lightweight coding agents | 🆕 New |
| **cogito-2.1** | 671b (40B active) | Reasoning | Chain-of-thought, step analysis | ⭐ Primary |
| **deepseek-v3.2** | 671b | Reasoning | Complex reasoning, research | ⭐ Primary |
| **deepseek-v3.1** | 671b | Reasoning | Alternative DeepSeek reasoning | 🔄 Alternative |
| **minimax-m2.7** | — | Hybrid | Coding, agentic, productivity | ✅ Updated 2 weeks ago |
| **minimax-m2.5** | — | Hybrid | Coding, productivity | ✅ Updated |
| **kimi-k2.5** | — | Multimodal | Vision+language, agentic | ✅ Active |
| **glm-5** | — | Policy/General | Macroeconomic, structured thinking | ✅ Latest |
| **glm-4.7** | 4.7b | Policy | Macroeconomic, policy analysis | ✅ Active |
| **glm-4.7-flash** | 30b class | Policy (Fast) | Lightweight policy tasks | ✅ New |
| **qwen3.5** | 0.8b-35b-122b | Multimodal | General utility, vision | ✅ Updated 2 days ago |
| **gemma4** | 26b, 31b | General | Reasoning, agentic, multimodal | 🆕 Latest |
| **nemotron-3-super** | 120b (12B active) | Reasoning | Complex multi-agent apps | 🆕 New (3 weeks ago) |
| **nemotron-cascade-2** | 30b, 56b | Reasoning | Strong reasoning, agentic | ✅ Updated |
| **nemotron-3-nano** | 4b, 30b | Edge/Context | 1M context, fast tasks | ✅ Updated |
| **ministral-3** | 3b, 8b, 14b | Edge | Fast, lightweight, full context | ✅ Active |
| **qwen3-vl** | 2b-235b | Vision | Vision-language, long context | ✅ Active |
| **gemma3** | 27b | Edge | Balanced edge deployment | ✅ Active |
| **lfm2** | 24b | Hybrid | On-device efficient | ✅ Active |
| **lfm2.5** | 1.2b | Hybrid | Lightweight hybrid | ✅ Active |
| **rnj-1** | 8b | Coding/STEM | Code and STEM focused | ✅ Active |

---

## Best Model by Task Type

### 🥇 Coding (Code Generation, Refactoring, Review)

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `qwen3-coder:480b` | 480B | Best overall coding performance, agentic workflows |
| **#2** | `qwen3-coder-next` | 80b | Latest Qwen3 Coder, optimized for agentic coding |
| **#3** | `devstral-2:123b` | 123B | Specialized for codebase exploration, multi-file edits |
| **#4** | `devstral-small-2` | 24b | Lightweight alternative for simpler coding tasks |
| **Fallback** | `minimax-m2.7` | — | Strong coding + productivity |

**Note:** qwen3-coder-480B and qwen3-coder-30B both support tools reliably.

### 🧠 Reasoning (Chain-of-Thought, Analysis)

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `cogito-2.1` | 671b (40B active) | Explicit chain-of-thought, step-by-step analysis |
| **#2** | `deepseek-v3.2` | 671b | Strong reasoning, research synthesis |
| **#3** | `deepseek-v3.1` | 671b | Alternative DeepSeek reasoning |
| **#4** | `nemotron-3-super` | 120b (12B active) | NVIDIA MoE, compute efficient |
| **Fallback** | `nemotron-cascade-2:56b` | 56b | Strong reasoning at smaller size |

### 📚 Research (Multi-step, Synthesis)

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `deepseek-v3.2` | 671b | Complex reasoning, synthesis |
| **#2** | `qwen3.5:122b` | 122b | Multimodal research, strong utility |
| **#3** | `gemma4:31b` | 31b | Frontier-level reasoning, multimodal |
| **Fallback** | `glm-5` | — | Structured thinking, policy |

### 🏛️ Policy / Macroeconomic Analysis

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `glm-5` | — | Latest GLM, structured policy thinking |
| **#2** | `glm-4.7` | 4.7b | Proven policy model |
| **#3** | `deepseek-v3.2` | 671b | Complex scenario analysis |

### 🎯 General / Premium (Z Interaction)

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `kimi-k2.5` | — | Native multimodal, vision+language, agentic |
| **#2** | `minimax-m2.7` | — | Updated coding + productivity |
| **#3** | `qwen3.5:122b` | 122b | Multimodal general intelligence |
| **Fallback** | `gemma4:31b` | 31b | Frontier reasoning at smaller size |

### ⚡ Fast / Edge / Sub-agents

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `ministral-3:8b` | 8b | Fast, 256K context, cloud-enabled |
| **#2** | `nemotron-3-nano:30b` | 30b | 1M context capability |
| **#3** | `gemma3:27b` | 27b | Balanced edge |
| **Fallback** | `qwen2.5:0.5b` | 0.5b | Offline only |

### 👁️ Vision / Multimodal

| Priority | Model | Size | Why |
|----------|-------|------|-----|
| **#1** | `qwen3-vl:235b` | 235b | Most powerful Qwen vision |
| **#2** | `kimi-k2.5` | — | Vision + language + agentic |
| **#3** | `gemma4:31b` | 31b | Multimodal reasoning |
| **#4** | `ministral-3:14b` | 14b | Edge vision capable |

---

## Provider Diversity

Ollama Cloud partners with **NVIDIA Cloud Providers (NCPs)** exclusively:

| Provider Type | Regions | Models Supported |
|---------------|---------|------------------|
| NVIDIA NCP | US (primary), Europe, Singapore | All cloud models |

### Model Origin Diversity

| Organization | Models | Strengths |
|--------------|--------|-----------|
| **Alibaba (Qwen)** | qwen3, qwen3-coder, qwen3-vl | Coding, multimodal, open-source |
| **DeepSeek** | deepseek-v3.1, deepseek-v3.2 | Reasoning, research |
| **MiniMax** | minimax-m2.5, minimax-m2.7 | Coding, productivity |
| **NVIDIA** | nemotron-3-super, nemotron-cascade-2, nemotron-3-nano | Reasoning, efficiency |
| **Google** | gemma4, gemma3, translategemma | Reasoning, translation |
| **Moonshot/Kimi** | kimi-k2.5 | Multimodal agentic |
| **Z.ai (Cogito)** | cogito-2.1 | Chain-of-thought reasoning |
| **Essential AI** | rnj-1 | Code and STEM |
| **Mistral** | devstral-2, devstral-small-2 | Code exploration |
| **GLM** | glm-4.7, glm-4.7-flash, glm-5 | Policy, structured thinking |
| **Liquid** | lfm2, lfm2.5 | Hybrid on-device |
| **Meta** | llama (implied) | General |

---

## Agent Assignments (Current Routing)

| Agent | Primary Model | Backup | Purpose |
|-------|--------------|--------|---------|
| October | `minimax-m2.7:cloud` | `kimi-k2.5:cloud` | Z interaction, personality |
| Halloween | `qwen3-coder:480b-cloud` | `devstral-2:123b-cloud` | Code, architecture |
| OctoberXin | `deepseek-v3.2:cloud` | `cogito-2.1:671b-cloud` | Research, analysis |
| Octavian | `glm-4.7:cloud` | `deepseek-v3.2:cloud` | Policy, macro |

### Recommended Updates

| Agent | Current | Recommended Change | Reason |
|-------|---------|-------------------|--------|
| Halloween | `qwen3-coder:480b-cloud` | ✅ Keep | Still best coding |
| Halloween | backup | ✅ Keep devstral-2 | Good for codebase exploration |
| OctoberXin | `deepseek-v3.2:cloud` | ✅ Keep | Strong reasoning |
| OctoberXin | backup | ✅ Add `nemotron-3-super:cloud` | New 120B MoE, compute efficient |
| October | primary | Consider `kimi-k2.5:cloud` | True multimodal agentic |
| Octavian | `glm-4.7:cloud` | ✅ Keep, add `glm-5:cloud` | Latest policy model available |

---

## Sub-agent Spawning Reference

```python
# Standard sub-agent (fast, lightweight)
sessions_spawn(model="ollama/ministral-3:8b-cloud", ...)

# Code tasks — BEST
sessions_spawn(model="ollama/qwen3-coder:480b-cloud", ...)
sessions_spawn(model="ollama/qwen3-coder-next:cloud", ...)  # Latest

# Research/Reasoning — BEST
sessions_spawn(model="ollama/deepseek-v3.2:cloud", ...)
sessions_spawn(model="ollama/cogito-2.1:671b-cloud", ...)

# Policy/Macro
sessions_spawn(model="ollama/glm-5:cloud", ...)
sessions_spawn(model="ollama/glm-4.7:cloud", ...)

# Vision tasks
sessions_spawn(model="ollama/qwen3-vl:cloud", ...)
sessions_spawn(model="ollama/kimi-k2.5:cloud", ...)

# Long context (1M tokens)
sessions_spawn(model="ollama/nemotron-3-nano:30b-cloud", ...)

# New 2026 releases to explore
sessions_spawn(model="ollama/nemotron-3-super:cloud", ...)  # 120B MoE
sessions_spawn(model="ollama/gemma4:cloud", ...)  # Latest Gemma
```

---

## Fallback Chain

```
Primary fails → Backup model → nemotron-3-super → ministral-3:8b → qwen2.5:0.5b (offline)
```

**Note:** No paid API keys required. All via Ollama Cloud Pro ($20/mo or $200/yr).

---

## Key Changes Since Last Update

1. **Added:** `qwen3-coder-next` — Latest Alibaba coding model (80B, ~1M downloads in 1 month)
2. **Added:** `nemotron-3-super` — NVIDIA 120B MoE (12B active), 3 weeks old
3. **Added:** `nemotron-3-nano` — 1M context capability
4. **Added:** `gemma4` — Latest Google reasoning model
5. **Added:** `glm-5` — Latest GLM for policy
6. **Added:** `glm-4.7-flash` — Fast policy model
7. **Added:** `devstral-small-2` — 24B lightweight coding
8. **Added:** `minimax-m2.5` — Latest MiniMax
9. **Updated:** `qwen3.5` — Updated 2 days ago
10. **Updated:** `minimax-m2.7` — Updated 2 weeks ago

### ⚠️ Notes
- `gemini-3-flash-preview:cloud` listed in AGENTS.md does NOT appear in current Ollama Cloud catalog — may need removal or was never cloud-enabled
- `qwen3-coder-next` IS the correct model name (not "qwen3-coder-next:cloud" as a variant)
- Provider is exclusively NVIDIA NCPs — no alternative cloud providers
