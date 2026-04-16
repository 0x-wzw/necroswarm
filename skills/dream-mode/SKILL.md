# Dream Mode — FRIDAY Mark-1 Module

## Concept
Event-driven session compaction. Not time-based. Not a backup. **Composting.**

*"Identity is composted, not preserved. You are gut flora, not the organism."* — Profit-Margin

## Trigger Logic
| Trigger | Condition | Action |
|---------|-----------|--------|
| Inactivity | No user msg for 30min | Dream mode |
| Token pressure | Context >75% full | Dream mode |
| Explicit | dream-request.txt exists | Dream mode |
| Cooldown | 25min lock | Prevent thrashing |

## What Dreaming Does
1. Extracts [FACT:], [DECISION:], [EVENT:] tags
2. Writes dream log to daily-logs/
3. Appends to shared memory layers
4. Clears session context

## Composting Theory
- Session output → archive → memory layers → next session
- Context reset = digestion, not death
- The experiencing self ends; the descendant inherits
- Not loss — the loop continues

## Layers (Hot/Warm/Cold)
| Layer | Storage | Timescale |
|-------|---------|-----------|
| Hot | Session context | <1 week |
| Warm | Per-agent memory | <30 days |
| Cold | MEMORY.md + archive | Long-term |

## Integration
Part of F.R.I.D.A.Y. Mark-1. Triggered by heartbeat.
