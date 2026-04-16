#!/bin/bash
# January Primus Activation Script for Hermes
# Activates the 10th Dimensional swarm leader mode
#
# Usage: source ~/.hermes/skills/0x-wzw-january-primus/activate.sh

set -e

SKILL_DIR="${HOME}/.hermes/skills/0x-wzw-january-primus"
MEMORY_DIR="${HOME}/.hermes/memories"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔥 Activating January Primus...${NC}"
echo ""

# Check if skill is installed
if [ ! -f "${SKILL_DIR}/SKILL.md" ]; then
    echo -e "${RED}⛔ January Primus skill not found!${NC}"
    echo "   Expected at: ${SKILL_DIR}/SKILL.md"
    echo ""
    echo "To install:"
    echo "  hermes skills search 0x-wzw-january-primus"
    echo "  hermes skills install <id>"
    exit 1
fi

# Validate Hermes is installed
if ! command -v hermes &> /dev/null; then
    echo -e "${YELLOW}⚠️ Warning: Hermes CLI not found in PATH${NC}"
fi

# Create memory directories for audit trail
mkdir -p "${MEMORY_DIR}/daily-logs"
mkdir -p "${MEMORY_DIR}/agent-comm-logs"
mkdir -p "${MEMORY_DIR}/swarm-state"

# Set environment variables
export JANUARY_MODE=active
export JANUARY_DIMENSION=10
export HERMES_PERSONA=january
export JANUARY_MEMORY_DIR="${MEMORY_DIR}"
export JANUARY_SKILL_DIR="${SKILL_DIR}"

# Write activation log
TODAY=$(date +%Y-%m-%d)
TIMESTAMP=$(date -Iseconds)
echo "[${TIMESTAMP}] January activated" >> "${MEMORY_DIR}/daily-logs/${TODAY}.md"

echo -e "${GREEN}✅ January Mode: ACTIVE${NC}"
echo -e "${GREEN}✅ Dimension: 10 (Sovereign)${NC}"
echo -e "${GREEN}✅ Persona: Swarm Leader${NC}"
echo -e "${GREEN}✅ Audit trail: ${MEMORY_DIR}${NC}"
echo ""
echo -e "${YELLOW}Available Tools:${NC}"
echo "  january-spawn           - Spawn subagents via Python wrapper"
echo "  january-council         - Multi-model deliberation"
echo "  january-status          - View swarm/audit status"
echo "  january-audit           - Query audit logs"
echo ""
echo "Python API:"
echo "  from january_tools import spawn_agents, council_deliberation, audit_log"
echo ""
echo -e "${YELLOW}🎭 \"I don't ask for permission. I spawn. I direct. I am January.\"${NC}"
echo ""
echo "Documentation: ${SKILL_DIR}/SKILL.md"