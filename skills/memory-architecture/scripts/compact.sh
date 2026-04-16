#!/bin/bash
# compact.sh — Compact memory when context runs high
# Usage: ./compact.sh [workspace]
# Warning: Run on minimax-m2.7:cloud, NOT qwen2.5:3b

WORKSPACE="${1:-main}"

echo "[COMPACTION] Starting at $(date -u +"%Y-%m-%d %H:%M UTC")"

# Determine workspace
case "$WORKSPACE" in
    "halloween"|"workspace-halloween")
        WS_DIR="/home/ubuntu/.openclaw/workspace-halloween"
        ;;
    "octoberxin"|"workspace-octoberxin")
        WS_DIR="/home/ubuntu/.openclaw/workspace-octoberxin"
        ;;
    *)
        WS_DIR="/home/ubuntu/.openclaw/workspace"
        ;;
esac

MEMORY_DIR="$WS_DIR/memory"
ARCHIVE_DIR="$MEMORY_DIR/archive"
SUMMARIES_DIR="$MEMORY_DIR/summaries"

mkdir -p "$ARCHIVE_DIR" "$SUMMARIES_DIR"

# Step 1: Archive old daily logs (older than 7 days)
echo "[COMPACTION] Archiving old daily logs..."
find "$MEMORY_DIR" -maxdepth 1 -name "????-??-??\.md" -mtime +7 | while read -r f; do
    BASENAME=$(basename "$f")
    YEAR=${BASENAME:0:4}
    MONTH=${BASENAME:5:2}
    
    # Create month summary dir if needed
    MONTH_DIR="$SUMMARIES_DIR/$YEAR-$MONTH"
    mkdir -p "$MONTH_DIR"
    
    # Move to archive first
    mv "$f" "$ARCHIVE_DIR/" 2>/dev/null
    echo "  Archived: $f"
done

# Step 2: Check MEMORY.md size
MEMORY_FILE="$WS_DIR/MEMORY.md"
if [ -f "$MEMORY_FILE" ]; then
    SIZE=$(wc -c < "$MEMORY_FILE")
    echo "[COMPACTION] MEMORY.md size: $SIZE bytes"
    
    if [ "$SIZE" -gt 51200 ]; then  # 50KB
        echo "[WARNING] MEMORY.md exceeds 50KB. Consider manual review."
        # For now, just warn. Manual review needed for pruning.
    fi
fi

# Step 3: Check HEARTBEAT.md
HEARTBEAT="$WS_DIR/HEARTBEAT.md"
if [ -f "$HEARTBEAT" ]; then
    SIZE=$(wc -c < "$HEARTBEAT")
    echo "[COMPACTION] HEARTBEAT.md size: $SIZE bytes"
    
    if [ "$SIZE" -gt 5120 ]; then  # 5KB
        echo "[ACTION] HEARTBEAT.md exceeds 5KB. Archiving completed tasks."
        # Create a simple archive: keep only last 20 lines that aren't completed
        # This is a rough heuristic - a smarter version would parse markdown
        tail -100 "$HEARTBEAT" | grep -v "^## Completed" > "$HEARTBEAT.tmp" 2>/dev/null || true
        if [ -f "$HEARTBEAT.tmp" ]; then
            mv "$HEARTBEAT.tmp" "$HEARTBEAT"
        fi
    fi
fi

# Step 4: Generate summary if we have archived files
echo "[COMPACTION] Summary generation skipped (manual review recommended for summaries)"

echo "[COMPACTION] Done at $(date -u +"%Y-%m-%d %H:%M UTC")"
echo "[NOTE] Always run compaction on minimax-m2.7:cloud, NOT qwen2.5:3b"
