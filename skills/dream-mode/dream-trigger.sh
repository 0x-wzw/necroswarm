#!/bin/bash
#===========================================================
# Dream Trigger — Called by heartbeat every 30 min
# Checks: inactivity | token pressure | sub-agent state
# If ANY trigger fires → runs dream-mode.sh
#===========================================================

set -euo pipefail

# --- Config ---
HEARTBEAT_DIR="/home/ubuntu/.openclaw/workspace/heartbeat"
DREAM_MODE_SCRIPT="/home/ubuntu/.openclaw/workspace/memory/dream-mode.sh"
LAST_MSG_FILE="${HEARTBEAT_DIR}/last-user-message.txt"
SESSION_FILE="${SESSION_FILE:-/tmp/openclaw-session-context.txt}"
SUBAGENT_COUNT_FILE="${HEARTBEAT_DIR}/active-subagents.txt"
LOCK_FILE="${HEARTBEAT_DIR}/dream-lock.txt"
COOLDOWN_MINUTES=25  # Prevent rapid re-triggering

INACTIVITY_MINUTES="${INACTIVITY_MINUTES:-30}"
TOKEN_THRESHOLD="${TOKEN_THRESHOLD:-75}"

# --- Check cooldown ---
if [[ -f "$LOCK_FILE" ]]; then
    LOCK_TIME=$(cat "$LOCK_FILE")
    LOCK_EPOCH=$(date -d "$LOCK_TIME" +%s 2>/dev/null || echo "0")
    NOW_EPOCH=$(date +%s)
    MINUTES_SINCE_LOCK=$(( (NOW_EPOCH - LOCK_EPOCH) / 60 ))
    if [[ $MINUTES_SINCE_LOCK -lt $COOLDOWN_MINUTES ]]; then
        echo "[Dream Trigger] Cooldown active (${MINUTES_SINCE_LOCK}/${COOLDOWN_MINUTES}min). Skipping."
        exit 0
    fi
fi

echo "[Dream Trigger] Running checks at $(date +"%Y-%m-%d %H:%M UTC")"

TRIGGERED=0
REASON=""

#===========================================================
# CHECK 1: Inactivity
#===========================================================

if [[ -f "$LAST_MSG_FILE" ]]; then
    LAST_MSG_TIME=$(cat "$LAST_MSG_FILE" 2>/dev/null || echo "")
    if [[ -n "$LAST_MSG_TIME" ]]; then
        LAST_MSG_EPOCH=$(date -d "$LAST_MSG_TIME" +%s 2>/dev/null || echo "0")
        NOW_EPOCH=$(date +%s)
        MINUTES_SINCE=$(( (NOW_EPOCH - LAST_MSG_EPOCH) / 60 ))
        if [[ $MINUTES_SINCE -ge $INACTIVITY_MINUTES ]]; then
            TRIGGERED=1
            REASON="inactivity (${MINUTES_SINCE}min > ${INACTIVITY_MINUTES}min)"
            echo "[Dream Trigger] INACTIVITY TRIGGER: ${MINUTES_SINCE}min idle"
        fi
    fi
fi

#===========================================================
# CHECK 2: Token threshold
#===========================================================

if [[ -f "$SESSION_FILE" ]]; then
    SESSION_SIZE=$(wc -c < "$SESSION_FILE" 2>/dev/null || echo "0")
    CURRENT_TOKENS=$((SESSION_SIZE / 4))
    # Threshold: 75% of 100k context window = 75k tokens
    # User-configurable via TOKEN_THRESHOLD env var (percentage)
    if [[ $CURRENT_TOKENS -gt 0 ]]; then
        # Rough check: if session file > 300KB, likely >75% of 100k context
        # 300KB / 4 = 75k tokens
        TOKEN_CHECK=$((TOKEN_THRESHOLD * 3000))  # scale: 75% = 225000 bytes
        if [[ $SESSION_SIZE -gt $TOKEN_CHECK ]]; then
            TRIGGERED=1
            REASON="token_threshold (~${CURRENT_TOKENS} tokens)"
            echo "[Dream Trigger] TOKEN TRIGGER: ~${CURRENT_TOKENS} tokens (${TOKEN_THRESHOLD}% threshold)"
        fi
    fi
fi

#===========================================================
# CHECK 3: Explicit trigger (sub-agent completion)
#===========================================================

if [[ -f "${HEARTBEAT_DIR}/dream-request.txt" ]]; then
    TRIGGERED=1
    REASON="explicit_request"
    echo "[Dream Trigger] EXPLICIT REQUEST found"
    rm -f "${HEARTBEAT_DIR}/dream-request.txt"
fi

#===========================================================
# CHECK 4: Sub-agent storm (optional safety)
#===========================================================

if [[ -f "$SUBAGENT_COUNT_FILE" ]]; then
    SUBAGENT_COUNT=$(cat "$SUBAGENT_COUNT_FILE" 2>/dev/null || echo "0")
    if [[ $SUBAGENT_COUNT -gt 5 ]]; then
        echo "[Dream Trigger] WARNING: High sub-agent count: $SUBAGENT_COUNT"
        # Not a trigger by default, just a warning
    fi
fi

#===========================================================
# FIRE: Run dream mode if triggered
#===========================================================

if [[ $TRIGGERED -eq 1 ]]; then
    echo "[Dream Trigger] FIRES → Running dream-mode.sh (reason: $REASON)"
    # Write cooldown lock
    date +"%Y-%m-%d %H:%M UTC" > "$LOCK_FILE"
    # Run compaction
    bash "$DREAM_MODE_SCRIPT"
    echo "[Dream Trigger] Dream complete."
else
    echo "[Dream Trigger] All checks passed. No trigger."
fi

exit 0
