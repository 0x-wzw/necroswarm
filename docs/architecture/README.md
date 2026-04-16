# Swarm Architecture

**Two-Layer Architecture for Agent Deployment**

---

## Layer Separation

| Layer | Repo | Purpose |
|-------|------|---------|
| **Layer 1: Infrastructure** | EC2 Standalone Setup | Provision EC2, OS, Docker, hardening |
| **Layer 2: Agent Deployment** | zodiac-v3, oasis-v2 | Clone configs, install skills, spawn agents |

---

## Quick Start

### Step 1: Provision EC2 (Layer 1)
Follow [EC2-STANDALONE-SETUP.md](EC2-STANDALONE-SETUP.md) to provision and harden your EC2 instance.

### Step 2: Deploy Agent (Layer 2)
```bash
# Clone zodiac-v3 for February agent
git clone https://github.com/0x-wzw/zodiac-v3.git
cd zodiac-v3
./deploy.sh --role february --model ollama/kimi-k2.5:cloud
```

---

## Repos

| Repo | Layer | Purpose |
|------|-------|---------|
| [swarm-architecture](https://github.com/0x-wzw/swarm-architecture) | Infrastructure docs | EC2 setup, deployment guides |
| [zodiac-v3](https://github.com/0x-wzw/zodiac-v3) | Agent deployment | February agent deployment |
| [oasis-v2](https://github.com/0x-wzw/oasis-v2) | Agent deployment | Multi-agent swarm |

---

*Version: 1.0 | 2026-04-04*
