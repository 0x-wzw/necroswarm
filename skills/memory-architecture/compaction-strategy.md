# Memory Compaction Strategy

## Why Compaction?

Context windows are finite. Without active compaction, a long-running agent system will:

1. **Hit the context ceiling** — Model stops accepting new input
2. **Lose coherence** — Old context gets dropped, agent forgets who it is
3. **Drift identity** — Without SOUL.md reinforcement, persona blurs

Compaction is the discipline that keeps the system lean and coherent.

## Compaction Triggers

### Automatic Triggers
- Context window exceeds 80% capacity
- Daily review (scheduled)
- After major events (new agent, infrastructure change, crisis)

### Manual Triggers
```bash
bash skills/memory-architecture/scripts/compact.sh
```

### Warning Signs (Run Compaction Now)
- Model starts repeating itself
- Agent forgets recent context mid-conversation
- "Context window exceeded" errors
- Identity drift (agent confused about role)

## The Compaction Process

### Step 1: Assess

Check current context state:
- How many daily log files exist?
- How large are the main memory files?
- What's the HEARTBEAT.md state?

### Step 2: Archive Daily Logs

Move session-by-session details from daily memory files into summary files.

**Before:**
```
memory/
├── 2026-03-18.md  # 50 lines of session notes
├── 2026-03-19.md  # 80 lines of session notes  
├── 2026-03-20.md  # 30 lines (today, partial)
```

**After:**
```
memory/
├── 2026-03-18.md
├── 2026-03-19.md
├── 2026-03-20.md
└── summaries/
    └── 2026-03-week-3.md  # Compressed summary
```

### Step 3: Prune Redundant Entries

Look for:
- Duplicate facts (same thing recorded in MEMORY.md and daily logs)
- Outdated information (old IPs, old routing rules)
- Trivial details (things that don't need to be remembered)

### Step 4: Update Layer Files

- **MEMORY.md**: Move durable facts from daily logs into long-term memory
- **HEARTBEAT.md**: Archive completed tasks, keep pending ones
- **AGENTS.md**: Remove stale teammate notes

### Step 5: Verify

After compaction:
1. Read the compacted MEMORY.md
2. Confirm key facts are present
3. Confirm persona (SOUL.md) is still reinforced
4. Confirm routing rules (AGENTS.md) are current

## Compaction Thresholds

| File | Size Warning | Action |
|------|-------------|--------|
| MEMORY.md | > 50KB | Review and prune |
| HEARTBEAT.md | > 5KB | Archive completed tasks |
| Daily logs | > 20 files | Archive to summaries |
| Per-agent MEMORY.md | > 30KB | Agent-specific compaction |

## What NOT to Compact

- **SOUL.md**: Never compact. Persona must remain intact.
- **USER.md**: Rarely changes. Don't touch.
- **TOOLS.md**: Only update, don't compact.

## The Cost of Not Compacting

We learned this the hard way:

1. **Session 1 (March 18)**: No compaction needed yet
2. **Session 2 (March 19)**: First signs of context creep
3. **Session 3 (March 20)**: qwen2.5:3b went zombie trying to compact its own context

The qwen2.5:3b zombie problem: this model locks up on sustained context-heavy operations. Use **minimax-m2.7:cloud** for any compaction work. Never run memory compaction on a small model.

## Post-Compaction Checklist

- [ ] MEMORY.md reviewed and pruned
- [ ] Daily logs archived to summaries
- [ ] HEARTBEAT.md updated (completed tasks archived)
- [ ] AGENTS.md checked for staleness
- [ ] SOUL.md read (reinforce persona)
- [ ] Context verified (can answer "who am I, what am I doing")

## Automation

For now, compaction is manual. A cron job can be set up:
```bash
# Every Sunday at 3am UTC
0 3 * * 0 cd ~/.openclaw/workspace && bash skills/memory-architecture/scripts/compact.sh >> memory/compaction.log 2>&1
```

Until that's stable, run it manually when you see warning signs.
