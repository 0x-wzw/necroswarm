---
name: find-skills
description: Discover and install agent skills from ClawHub. Use when looking for a skill to solve a specific problem (e.g. "how do I do X", "find a skill for X"). Uses the clawhub CLI to search, install, update, and publish skills. Triggered by phrases like "how do I do X", "find a skill for X", or interest in extending capabilities.
---

# Find Skills

Search ClawHub for installable agent skills using the clawhub CLI.

## Prerequisites

```bash
npm install -g clawhub
```

## Usage

```bash
# Search for a skill
clawhub search "DeFi"

# Install a skill
clawhub install DeFi-research

# List installed skills
clawhub list

# Update a skill to latest
clawhub update defi-analyst

# Publish a skill
clawhub publish /path/to/your/skill
```

## When to Use

- Z asks "how do I do X?"
- Z asks "is there a skill for X?"
- Z wants to extend capabilities
- Z expresses interest in a new integration

## How It Works

1. Search clawhub.com for matching skills
2. Review skill documentation
3. Install with `clawhub install`
4. Skill is copied to `~/.openclaw/skills/`

## Example Workflow

```
User: "I need to analyze crypto portfolios automatically"
Agent: *searches ClawHub*
→ clawhub search "crypto portfolio"
→ clawhub install defi-analyst
→ skill installed, explains how to use
```
