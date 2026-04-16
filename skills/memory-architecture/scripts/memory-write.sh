#!/bin/bash
# memory-write.sh — Write to daily memory files
# Usage: ./memory-write.sh <workspace> <message>
# Example: ./memory-write.sh "Halloween" "Spawned sub-agent for repo setup"

WORKSPACE="${1:-main}"
MESSAGE="${2:-}"
AGENT_NAME="${3:-$(hostname)}"
TIMESTAMP=$(date -u +"%Y-%m-%d %H:%M UTC")

if [ -z "$MESSAGE" ]; then
    echo "Usage: $0 <workspace> <message> [agent_name]"
    exit 1
fi

# Determine memory directory
case "$WORKSPACE" in
    "halloween"|"workspace-halloween")
        MEMORY_DIR="/home/ubuntu/.openclaw/workspace-halloween/memory"
        ;;
    "octoberxin"|"workspace-octoberxin")
        MEMORY_DIR="/home/ubuntu/.openclaw/workspace-octoberxin/memory"
        ;;
    *)
        MEMORY_DIR="/home/ubuntu/.openclaw/workspace/memory"
        ;;
esac

mkdir -p "$MEMORY_DIR"

TODAY=$(date -u +"%Y-%m-%d")
LOG_FILE="$MEMORY_DIR/$TODAY.md"

# Write entry
echo "## $TIMESTAMP [$AGENT_NAME]" >> "$LOG_FILE"
echo "$MESSAGE" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

echo "[OK] Wrote to $LOG_FILE"
