#!/bin/bash
# install-all.sh — Install all skills from swarm-agent-kit
# Usage: bash scripts/install-all.sh [--dry-run]

set -e

SKILLS_DIR="${HOME}/.openclaw/skills"
SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Swarm Agent Kit Installer ==="
echo "Source: ${SOURCE_DIR}"
echo "Target: ${SKILLS_DIR}"
echo ""

# Dry run mode
if [ "$1" = "--dry-run" ]; then
  echo "[DRY RUN] Would install:"
  ls -d "${SOURCE_DIR}/skills"/*/
  exit 0
fi

# Create target dir
mkdir -p "${SKILLS_DIR}"

# Install each skill
for skill in "${SOURCE_DIR}/skills"/*/; do
  skill_name=$(basename "$skill")
  
  if [ -f "${skill}/SKILL.md" ]; then
    echo "Installing ${skill_name}..."
    cp -r "$skill" "${SKILLS_DIR}/"
    echo "  ✓ ${skill_name} installed"
  else
    echo "  ✗ ${skill_name} missing SKILL.md — skipping"
  fi
done

echo ""
echo "=== Installation Complete ==="
echo "Installed skills:"
ls "${SKILLS_DIR}" | grep -v "^\." | sort
echo ""
echo "Run 'bash scripts/validate.sh' to verify all skills."
