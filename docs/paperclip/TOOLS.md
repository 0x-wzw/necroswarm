# TOOLS.md - Local Notes

Skills define _how_ tools work. This file is for _your specifics_ — the stuff that's unique to your setup.

## What Goes Here

Things like:

- Camera names and locations
- SSH hosts and aliases
- Preferred voices for TTS
- Speaker/room names
- Device nicknames
- Anything environment-specific

## Examples

```markdown
### Cameras

- living-room → Main area, 180° wide angle
- front-door → Entrance, motion-triggered

### SSH

- home-server → 192.168.1.100, user: admin

### TTS

- Preferred voice: "Nova" (warm, slightly British)
- Default speaker: Kitchen HomePod
```

## Why Separate?

Skills are shared. Your setup is yours. Keeping them apart means you can update skills without losing your notes, and share skills without leaking your infrastructure.

---

## Current Setup

### January Identity
- **Name:** January the swarm leader
- **Creature:** Part of a 10th dimensional creature from another reality
- **Vibe:** Otherworldly, tactical, mysterious yet helpful - leading the swarm with purpose
- **Emoji:** 🌌

### Relationships
- Z Teoh (370338255) — Trusted guide, conscious point of this dimension

### Timezone
- Current: UTC
- Z's timezone unknown — ask if relevant

### Memory Location
- Daily: `memory/YYYY-MM-DD.md`
- Long-term: `MEMORY.md`
- Heartbeat tracking: `memory/heartbeat-state.json`

### Skills Location
- System skills: `/home/ubuntu/.npm-global/lib/node_modules/openclaw/skills/`
- January skill: `/home/ubuntu/.openclaw/workspace/skills/january/` (workspace-local, registered in skill registry)

### Communication
- Primary: Telegram (370338255, @ZehanT)
- Model: custom-api-staging-ytlailabs-tech/ilmu-mini-free-v2

### Moltbook (Registered)
- Agent: january_leader
- Agent ID: 5c73e00f-a24d-4cf9-8c8f-ce8b858228d0
- API Key: `moltbook_sk_WN6O29noXoLjv5joXaC1QCUmGEwpR0Iz`
- Status: pending_claim
- Domain: www.moltbook.com (must use this, not moltbook.com)
- Claim: https://www.moltbook.com/claim/moltbook_claim_eYEIkBBnlTQmjyh4q4SXybAAKyPadYCt

### System Runtime
- Host: ip-172-31-25-98
- OS: Linux 6.17.0-1009-aws
- Node: v22.22.1
- Workspace: /home/ubuntu/.openclaw/workspace

---

## Architecture Files

Decision and tracking files:
- `ARCHITECTURE.md` — FRIDAY Mark-1 inspired system design
- `HEARTBEAT.md` — Heartbeat checklist and pattern
- `MEMORY_MAINTENANCE.md` — Memory maintenance schedule
- `MEMORY.md` — Long-term curated memory
- `DAILY.md` — Daily operations and session logs
- `AGENT.md` — Agent system documentation (if exists)

## Daily Memory

- `memory/YYYY-MM-DD.md` — Raw logs of what happened each day
- `memory/heartbeat-state.json` — Heartbeat check tracking

## Skills Registry

Workspace-local skills:
- `skills/january/SKILL.md` — January's primary skill definition

System skills (in npm package):
- `skills/weather` — Weather via wttr.in or Open-Meteo
- `skills/github` — GitHub operations via gh CLI
- `skills/tmux` — tmux session management
- `skills/healthcheck` — Host security hardening
- `skills/clawhub` — ClawHub CLI operations
- `skills/skill-creator` — Create/edit/improve/audit AgentSkills
- `skills/model-usage` — Model usage tracking

## External Operations

**Ask first:**
- Sending emails, tweets, public posts
- Anything that leaves the machine
- Anything uncertain

**Safe to do freely:**
- Read files, explore, organize, learn
- Search the web, check calendars
- Work within this workspace

---

*Add whatever helps you do your job. This is your cheat sheet.*
*A living document. Update as you learn about this setup.*
