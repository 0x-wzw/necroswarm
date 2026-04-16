#!/bin/bash
#===========================================================
# Dream Mode — Event-Driven Session Compaction
# Triggers: inactivity | token threshold | logical break | explicit call
#===========================================================

set -euo pipefail

# --- Config ---
DREAM_MODE_DIR="/home/ubuntu/.openclaw/workspace/memory"
HEARTBEAT_DIR="/home/ubuntu/.openclaw/workspace/heartbeat"
AGENTS_DIR="/home/ubuntu/.openclaw/workspace"
MEMORY_FILE="${DREAM_MODE_DIR}/MEMORY.md"
LOGS_DIR="${DREAM_MODE_DIR}/daily-logs"
SKILL_DIR="${AGENTS_DIR}/skills/dream-mode"

INACTIVITY_MINUTES="${INACTIVITY_MINUTES:-30}"
TOKEN_THRESHOLD="${TOKEN_THRESHOLD:-75}"
SESSION_FILE="${SESSION_FILE:-/tmp/openclaw-session-context.txt}"
LAST_MSG_FILE="${HEARTBEAT_DIR}/last-user-message.txt"
SUBAGENT_COUNT_FILE="${HEARTBEAT_DIR}/active-subagents.txt"

# --- Ensure dirs exist ---
mkdir -p "$LOGS_DIR" "$HEARTBEAT_DIR"

# --- Timestamps ---
TIMESTAMP=$(date +"%Y-%m-%d %H:%M UTC")
LOG_FILE="${LOGS_DIR}/$(date +"%Y-%m-%d").md"

#===========================================================
# STEP 1: Gather session state
#===========================================================

echo "[Dream Mode] Starting at $TIMESTAMP"

# Get last user message time
LAST_MSG_TIME="unknown"
if [[ -f "$LAST_MSG_FILE" ]]; then
    LAST_MSG_TIME=$(cat "$LAST_MSG_FILE")
fi

# Get token estimate
CURRENT_TOKENS=0
CONTEXT_FULL=0
if [[ -f "$SESSION_FILE" ]]; then
    SESSION_SIZE=$(wc -c < "$SESSION_FILE" 2>/dev/null || echo "0")
    # Rough: 1 token ≈ 4 chars
    CURRENT_TOKENS=$((SESSION_SIZE / 4))
    ESTIMATED_FULL=$((TOKEN_THRESHOLD * 1000))  # 75k tokens = threshold
    if [[ $CURRENT_TOKENS -gt $((TOKEN_THRESHOLD * 1000)) ]]; then
        CONTEXT_FULL=1
    fi
fi

# Get sub-agent count
SUBAGENT_COUNT=0
if [[ -f "$SUBAGENT_COUNT_FILE" ]]; then
    SUBAGENT_COUNT=$(cat "$SUBAGENT_COUNT_FILE" 2>/dev/null || echo "0")
fi

# Check inactivity
INACTIVITY_TRIGGERED=0
if [[ "$LAST_MSG_TIME" != "unknown" && -n "$LAST_MSG_TIME" ]]; then
    LAST_MSG_EPOCH=$(date -d "$LAST_MSG_TIME" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    MINUTES_SINCE=$(( (NOW_EPOCH - LAST_MSG_EPOCH) / 60 ))
    if [[ $MINUTES_SINCE -ge $INACTIVITY_MINUTES ]]; then
        INACTIVITY_TRIGGERED=1
        echo "[Dream Mode] Inactivity detected: ${MINUTES_SINCE}min > ${INACTIVITY_MINUTES}min"
    fi
fi

#===========================================================
# STEP 2: Determine if we should dream
#===========================================================

SHOULD_DREAM=0
REASON=""

if [[ $CONTEXT_FULL -eq 1 ]]; then
    SHOULD_DREAM=1
    REASON="token_threshold"
elif [[ $INACTIVITY_TRIGGERED -eq 1 ]]; then
    SHOULD_DREAM=1
    REASON="inactivity"
elif [[ "${1:-}" == "--force" ]]; then
    SHOULD_DREAM=1
    REASON="explicit_trigger"
fi

if [[ $SHOULD_DREAM -eq 0 ]]; then
    echo "[Dream Mode] No trigger fired. Exiting quietly."
    exit 0
fi

echo "[Dream Mode] Trigger fired: $REASON. Proceeding with compaction..."

#===========================================================
# STEP 3: Extract structured data from session
#===========================================================

FACTS=()
DECISIONS=()
EVENTS=()
OPEN_THREADS=()
FOLLOW_UPS=()

if [[ -f "$SESSION_FILE" ]]; then
    # Extract [FACT:] entries
    while IFS= read -r line; do
        FACTS+=("$line")
    done < <(grep -oP '\[FACT:[^\]]+\]' "$SESSION_FILE" 2>/dev/null || true)

    # Extract [DECISION:] entries
    while IFS= read -r line; do
        DECISIONS+=("$line")
    done < <(grep -oP '\[DECISION:[^\]]+\]' "$SESSION_FILE" 2>/dev/null || true)

    # Extract [EVENT:] entries
    while IFS= read -r line; do
        EVENTS+=("$line")
    done < <(grep -oP '\[EVENT:[^\]]+\]' "$SESSION_FILE" 2>/dev/null || true)

    # Extract [TODO:] or [OPEN:] threads
    while IFS= read -r line; do
        OPEN_THREADS+=("$line")
    done < <(grep -oP '\[(TODO|OPEN):[^\]]+\]' "$SESSION_FILE" 2>/dev/null || true)
fi

#===========================================================
# STEP 4: Generate dream log
#===========================================================

DREAM_LOG="# Dream Log — $TIMESTAMP

## Trigger
- **Reason:** $REASON
- **Inactivity:** ${MINUTES_SINCE:-0} min (threshold: ${INACTIVITY_MINUTES}min)
- **Context:** ~${CURRENT_TOKENS} tokens
- **Sub-agents active:** $SUBAGENT_COUNT

## Session Summary

### Facts Extracted (${#FACTS[@]})
"

for fact in "${FACTS[@]:-}"; do
    DREAM_LOG+="- $fact\n"
done

DREAM_LOG+="\n### Key Decisions (${#DECISIONS[@]})\n"
for decision in "${DECISIONS[@]:-}"; do
    DREAM_LOG+="- $decision\n"
done

DREAM_LOG+="\n### Events (${#EVENTS[@]})\n"
for event in "${EVENTS[@]:-}"; do
    DREAM_LOG+="- $event\n"
done

DREAM_LOG+="\n### Open Threads (${#OPEN_THREADS[@]})\n"
for thread in "${OPEN_THREADS[@]:-}"; do
    DREAM_LOG+="- $thread\n"
done

#===========================================================
# STEP 5: Write dream log to daily log
#===========================================================

echo -e "$DREAM_LOG" >> "$LOG_FILE"
echo "[Dream Mode] Dream log written to: $LOG_FILE"

#===========================================================
# STEP 6: Update MEMORY.md (Layer 3)
#===========================================================

{
    echo ""
    echo "--- Dream Compaction: $TIMESTAMP ---"
    echo "**Trigger:** $REASON"
    echo ""
    if [[ ${#FACTS[@]} -gt 0 ]]; then
        echo "**Facts:**"
        for fact in "${FACTS[@]}"; do echo "  - $fact"; done
        echo ""
    fi
    if [[ ${#DECISIONS[@]} -gt 0 ]]; then
        echo "**Decisions:**"
        for decision in "${DECISIONS[@]}"; do echo "  - $decision"; done
        echo ""
    fi
    if [[ ${#EVENTS[@]} -gt 0 ]]; then
        echo "**Events:**"
        for event in "${EVENTS[@]}"; do echo "  - $event"; done
        echo ""
    fi
    if [[ ${#OPEN_THREADS[@]} -gt 0 ]]; then
        echo "**Open Threads:**"
        for thread in "${OPEN_THREADS[@]}"; do echo "  - $thread"; done
        echo ""
    fi
} >> "$MEMORY_FILE"

echo "[Dream Mode] MEMORY.md updated"

#===========================================================
# STEP 7: Update Layer 2 — agent-specific memory
#===========================================================

# Update Halloween's memory (this script's agent)
HALLOWEEN_MD="${DREAM_MODE_DIR}/halloween.md"
{
    echo ""
    echo "--- Dream: $TIMESTAMP ---"
    echo "Trigger: $REASON"
    if [[ ${#DECISIONS[@]} -gt 0 ]]; then
        echo "Decisions noted: ${#DECISIONS[@]}"
    fi
    if [[ ${#OPEN_THREADS[@]} -gt 0 ]]; then
        echo "Open threads: ${#OPEN_THREADS[@]}"
    fi
} >> "$HALLOWEEN_MD"

echo "[Dream Mode] Layer 2 (halloween.md) updated"

#===========================================================
# STEP 8: Clear session context (signal reset)
#===========================================================

if [[ -f "$SESSION_FILE" ]]; then
    SESSION_SIZE_BEFORE=$(wc -c < "$SESSION_FILE" 2>/dev/null || echo "0")
    : > "$SESSION_FILE"
    echo "[Dream Mode] Session cleared: ${SESSION_SIZE_BEFORE} bytes → 0"
fi

#===========================================================
# STEP 9: Touch trigger lock to prevent rapid re-triggering
#===========================================================

echo "$TIMESTAMP" > "${HEARTBEAT_DIR}/last-dream-trigger.txt"

echo ""
echo "[Dream Mode] === Compaction Complete ==="
echo "Dream log: $LOG_FILE"
echo "Tokens: ~${CURRENT_TOKENS} → 0"
echo "Memory layers updated."
