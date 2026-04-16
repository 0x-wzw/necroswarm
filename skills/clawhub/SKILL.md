---
name: clawhub
description: ClawHub CLI skill management. Search, install, update, and publish agent skills from clawhub.com. Use when Z wants to extend agent capabilities, find a skill for a specific task, or publish a new skill. Install via npm: npm install -g clawhub
---

# ClawHub Skill

Manage skills using the clawhub CLI.

## Install

```bash
npm install -g clawhub
```

## Commands

```bash
# Search for skills
clawhub search "DeFi"
clawhub search "twitter" --limit 10

# Install a skill
clawhub install defi-analyst

# List installed skills
clawhub list

# Update to latest version
clawhub update defi-analyst
clawhub update --all

# Publish a skill
clawhub publish /path/to/skill-folder

# Check skill info
clawhub info skill-name
```

## Skill Format

Published skills must follow the AgentSkills spec:

```
skill-name/
├── SKILL.md          # name + description + body
├── scripts/          # (optional)
└── references/       # (optional)
```

## Workflow

1. **Find** — `clawhub search "something"`
2. **Preview** — `clawhub info skill-name`
3. **Install** — `clawhub install skill-name`
4. **Use** — skill is now in `~/.openclaw/skills/`

## Publish Your Own

```bash
clawhub publish ./my-new-skill
```

Requires being logged in (`clawhub login`).

## Notes

- Skills install to `~/.openclaw/skills/` by default
- Override with `--path /custom/path`
- `clawhub update` fetches latest from registry
