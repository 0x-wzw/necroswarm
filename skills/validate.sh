#!/bin/bash
# validate.sh — Validate all skills in swarm-agent-kit
# Checks: SKILL.md present, valid format, scripts executable

set -e

SOURCE_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FAILED=0

echo "=== Skill Validation ==="
echo ""

for skill in "${SOURCE_DIR}/skills"/*/; do
  skill_name=$(basename "$skill")
  
  # Check SKILL.md exists
  if [ ! -f "${skill}/SKILL.md" ]; then
    echo "✗ ${skill_name}: SKILL.md missing"
    FAILED=$((FAILED + 1))
    continue
  fi
  
  # Check frontmatter has name + description
  if ! grep -q "^name:" "${skill}/SKILL.md"; then
    echo "✗ ${skill_name}: 'name:' field missing"
    FAILED=$((FAILED + 1))
  fi
  
  if ! grep -q "^description:" "${skill}/SKILL.md"; then
    echo "✗ ${skill_name}: 'description:' field missing"
    FAILED=$((FAILED + 1))
  fi
  
  # Check scripts are executable
  if [ -d "${skill}/scripts" ]; then
    for script in "${skill}/scripts/"*.sh; do
      if [ -f "$script" ]; then
        if [ ! -x "$script" ]; then
          echo "⚠ ${skill_name}: $(basename $script) not executable — fixing"
          chmod +x "$script"
        fi
      fi
    done
  fi
  
  # Check SKILL.md not empty
  if [ ! -s "${skill}/SKILL.md" ]; then
    echo "✗ ${skill_name}: SKILL.md is empty"
    FAILED=$((FAILED + 1))
    continue
  fi
  
  # Check for TODOs
  if grep -qi "TODO" "${skill}/SKILL.md"; then
    echo "⚠ ${skill_name}: contains TODOs"
  fi
  
  echo "✓ ${skill_name}"
done

echo ""
if [ $FAILED -eq 0 ]; then
  echo "=== All skills valid ==="
  exit 0
else
  echo "=== ${FAILED} skill(s) failed ==="
  exit 1
fi
