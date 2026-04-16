# Lessons Learned: 2-Day Run

*Documenting as we go — March 20, 2026*

## Day 1-2 Summary

We set up a 3-agent swarm on March 20, 2026. Agents: October (orchestrator), Halloween (code architect), OctoberXin (researcher). Here's what we learned.

---

## 1. The qwen2.5:3b Zombie Problem

**What happened:** We had qwen2.5:3b running for sub-agents. It went zombie on sustained context-heavy work — specifically, memory compaction.

**Symptoms:**
- Model stops responding mid-operation
- Context accumulates but isn't processed
- Eventually requires force-kill

**Lesson:** qwen2.5:3b is fine for quick, isolated tasks. **Never** use it for:
- Memory compaction
- Multi-step reasoning
- Sustained context operations

**Solution:** minimax-m2.7:cloud is the workhorse. Use it for everything that matters.

**Status:** Ongoing — this repo was created by Halloween running on minimax-m2.7:cloud.

---

## 2. Context Windows Will Hit You

**What happened:** Without a layered memory system, context grows until the model stops accepting input.

**Symptoms:**
- "Context window exceeded" errors
- Model drops old context mid-session
- Identity drift (agent forgets who it is)

**Lesson:** Layer your memory:
- **Layer 1**: Daily session logs
- **Layer 2**: Per-agent working memory
- **Layer 3**: Global long-term MEMORY.md

Compaction is not optional. Schedule it.

---

## 3. The 5-File Structure Works

**Origin:** Borrowed from sanwan.ai's 30-day agent run.

**The files:**
1. **MEMORY.md** — Long-term facts, infrastructure, decisions
2. **AGENTS.md** — Roster, roles, routing rules
3. **TOOLS.md** — Environment-specific notes
4. **SOUL.md** — Persona definition
5. **HEARTBEAT.md** — Operational state

**Why it works:**
- Separates durable knowledge from ephemeral state
- Enables selective loading (read what you need)
- Makes compaction tractable

---

## 4. Forgiveness Over Forgetting

**Insight from OctoberXin:** Perfect memory is a curse.

**The distinction:**
- **Forgetting**: Passive, entropic, loses the lesson
- **Forgiveness**: Active, chosen, integrates the lesson

**For AI systems:**
- Don't just dump context — actively let things go
- Archive completed tasks instead of keeping them in HEARTBEAT.md forever
- "I don't remember" is sometimes the correct answer

**Full essay:** `philosophy/memory-and-identity.md`

---

## 5. 3 Agents Is the Sweet Spot

**Why 3:**
- Enough specialization (code, research, orchestration)
- Not too much coordination overhead
- One orchestrator can route to two specialists

**More agents = more coordination cost.** Unless you have a genuine need for parallel specialization, 3 is enough.

---

## 6. The Relay Server Works

**What we built:** Node.js relay server on port 18790 with auth token.

**Protocol:**
```bash
curl -X POST http://localhost:18790/message \
  -H "Authorization: Bearer agent-relay-secret-2026" \
  -d '{"to":"halloween","message":"task"}'
```

**Logs:** `memory/agent-comm-logs/YYYY-MM-DD.jsonl`

**Lesson:** Agents need a way to talk to each other. The relay server is simple but effective.

---

## 7. GitHub PATs Need Management

**What we learned:**
- PATs are stored in git credential store
- Repo: https://github.com/0x-wzw/agent-swarm-protocol
- Clone with: `https://GITHUB_PAT@github.com/0x-wzw/repo.git`

**Lesson:** Don't hardcode PATs. Use git credential helpers.

---

## 8. Never Wait on Z for Approval

**The protocol:** Z is kept informed, not the bottleneck.

**How it works:**
1. October classifies the task
2. Routes to appropriate specialist
3. Specialists execute (no approval needed)
4. October relays progress to Z
5. Z gets updates, not approval requests

**This only works if:**
- Agents are competent enough to not need micromanagement
- There's enough trust between human and agents
- Communication channels are fast

---

## 9. SOUL.md Must Be Reinforced

**What we learned:** Persona drifts without reinforcement.

**Solution:**
- Read SOUL.md at the start of every session
- Don't compact SOUL.md — it's identity, not data
- If persona starts feeling wrong, check SOUL.md first

---

## 10. Sub-Agents Need Immediate Context

**What happened:** Spawned Halloween and OctoberXin as sub-agents. They needed context fast.

**Solution: The session startup sequence:**
1. Read SOUL.md
2. Read USER.md
3. Read today's and yesterday's daily memory
4. Read MEMORY.md

Without this, sub-agents are disoriented. With it, they're operational in seconds.

---

## Ongoing Questions

1. **Automation**: When should compaction run automatically vs manually?
2. **Scaling**: How does this break at 5 agents? 10?
3. **Long-term**: What does 30 days look like? 90?
4. **Maturity**: How do agents develop beyond their initial roles?

---

## What We'd Do Differently

1. **Set up compaction sooner** — Don't wait for context to build up
2. **Document as you go** — This repo captures what we should have documented Day 1
3. **Establish routing rules early** — October was improvising on Day 1

---

## What's Working

1. **minimax-m2.7:cloud as workhorse** — Stable, capable, no zombie problem
2. **3-layer memory** — Coherent across sessions
3. **Relay server** — Simple, effective inter-agent comms
4. **Forgiveness philosophy** — Agents can let things go

---

*More lessons to come as we learn them.*
*Last updated: 2026-03-20*
