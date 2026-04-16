# EC2 Standalone Setup Guide

**Layer 1: Infrastructure Provisioning**

This guide sets up the **environment** where agents will be spawned. It does NOT deploy agents — it prepares the EC2 instance to receive them.

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1: EC2 Standalone Setup (This Guide)            │
│  └── Provisions EC2, OS, Docker, dependencies           │
│  └── Sets up networking, security, users                │
│  └── Leaves instance ready to receive agent deployment   │
├─────────────────────────────────────────────────────────┤
│  LAYER 2: Agent Deployment Repos (zodiac-v3, oasis-v2) │
│  └── Clone agent configs onto provisioned EC2           │
│  └── Install skills, workflows, memories                 │
│  └── Spawn and configure agents                         │
└─────────────────────────────────────────────────────────┘
```

**Flow:**
```
1. Provision EC2 with this guide
2. SSH into fresh EC2
3. Run environment setup (Docker, Node.js, dependencies)
4. Clone zodiac-v3 or oasis-v2 repo
5. Run agent deployment script
6. Agent spawns and becomes operational
```

---

## Purpose

This standalone guide handles **infrastructure only**:
- EC2 instance launch and configuration
- OS setup, user management, security hardening
- Docker and dependency installation
- Network configuration (ports, firewall, VPN)
- Environment validation (ready to receive agent deployment)

**What it does NOT do:**
- Deploy agents (that's zodiac/oasis repos)
- Configure agent skills or memories
- Set up inter-agent communication
- Configure channel integrations (Telegram, Discord)

---

## Agent Deployment Repos

After provisioning EC2 with this guide, clone the appropriate deployment repo:

| Repo | Purpose | For |
|------|---------|-----|
| **[zodiac-v3](https://github.com/0x-wzw/zodiac-v3)** | February agent deployment | Chief of Staff / Operations |
| **[oasis-v2](https://github.com/0x-wzw/oasis-v2)** | Multi-agent orchestration | Swarm coordination |
| **[paperclip-orchestration-january](https://github.com/0x-wzw/paperclip-orchestration-january)** | January agent deployment | Commander / Philosopher |

**Flow:**
```bash
# After EC2 is provisioned and hardened

git clone https://github.com/0x-wzw/zodiac-v3.git
cd zodiac-v3
./deploy.sh --role february --model ollama/kimi-k2.5:cloud
```

---

## Prerequisites

- AWS account
- SSH key pair (.pem file)
- Basic understanding of AWS EC2

---

## Step 1: Launch EC2 Instance

### Via Console

1. Go to AWS EC2 Dashboard → Launch Instance
2. **Name:** openclaw-node
3. **AMI:** Ubuntu 22.04 LTS (or Amazon Linux 2023)
4. **Instance type:** See sizing below
5. **Key pair:** Select or create RSA .pem
6. **Network:** Default VPC (or private subnet for production)
7. **Firewall:** Create security group

### Security Group Rules

| Type | Port | Source | Purpose |
|------|------|--------|---------|
| SSH | 22 | Your IP only | Admin access |
| HTTP | 80 | Anywhere | Let's Encrypt (optional) |
| Custom | 18789 | Your IP or VPN | OpenClaw gateway (restrict in prod) |

### Instance Sizing

| Use Case | Instance | vCPU | RAM | Network | Monthly Cost |
|----------|----------|------|-----|---------|--------------|
| **Free tier** | t3.micro | 2 | 1 GB | 5 Gbps | ~$0 (12mo) |
| Light use | t3.small | 2 | 2 GB | 5 Gbps | ~$8-15 |
| Production | t3.medium | 2 | 4 GB | 5 Gbps | ~$15-20 |
| **Swarm node** | m7i-flex.large | 2 | **8 GB** | **12.5 Gbps** | ~$25-30 |
| Heavy workload | m7i-flex.xlarge | 4 | 16 GB | 12.5 Gbps | ~$50 |

**Recommended for swarm:** m7i-flex.large (free-tier eligible, 8GB RAM, 12.5Gbps network)

---

## Step 2: Connect via SSH

```bash
# Replace with your key path and EC2 IP
ssh -i /path/to/your-key.pem ubuntu@YOUR_EC2_PUBLIC_IP

# For Amazon Linux, user is:
ssh -i /path/to/your-key.pem ec2-user@YOUR_EC2_PUBLIC_IP
```

---

## Step 3: Install OpenClaw

### Option A: One-Line Installer (Recommended)

```bash
curl -fsSL https://openclaw.ai/install.sh | bash
```

### Option B: Manual Node.js + Install

```bash
# Install Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Verify
node -v  # Should be v22.x

# Install OpenClaw
npm install -g openclaw
```

---

## Step 4: Initial Setup

```bash
# Run setup wizard
openclaw setup

# Follow prompts:
# 1. Select LLM provider (Anthropic/OpenAI/DeepSeek/Ollama)
# 2. Enter API key
# 3. Select channel (optional - Telegram/Discord/WhatsApp)
# 4. Set workspace location
```

### Configure Ollama Cloud (Free Tier)

```bash
# If using Ollama Cloud (free with Pro)
openclaw config set providers.ollama_cloud.api_key YOUR_KEY
openclaw config set agents.defaults.model ollama/kimi-k2.5:cloud
```

---

## Step 5: Configure as Systemd Service

```bash
# Install systemd unit (keeps OpenClaw running 24/7)
sudo openclaw service install --systemd

# Enable and start
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Check status
sudo systemctl status openclaw
openclaw status

# View logs
journalctl -u openclaw -f
```

---

## Step 6: Production Hardening

### Create Dedicated User

```bash
# Create non-root user
sudo adduser openclaw
sudo usermod -aG sudo openclaw

# Copy SSH keys
sudo mkdir -p /home/openclaw/.ssh
sudo cp /home/ubuntu/.ssh/authorized_keys /home/openclaw/.ssh/
sudo chown -R openclaw:openclaw /home/openclaw/.ssh
sudo chmod 700 /home/openclaw/.ssh
sudo chmod 600 /home/openclaw/.ssh/authorized_keys

# Login as openclaw
ssh -i /path/to/key.pem openclaw@EC2_IP
```

### Change SSH Port

```bash
sudo vi /etc/ssh/sshd_config
# Change: Port 22 → Port 2222
# Change: PermitRootLogin no
# Change: PasswordAuthentication no

sudo systemctl restart sshd
```

### Configure UFW Firewall

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 2222/tcp  # New SSH port
sudo ufw enable
```

### Set API Spend Limits

```bash
# Anthropic: console.anthropic.com/settings/limits
# OpenAI: platform.billing.settings
# Set $20-30/month hard limit
```

### Backup Automation

```bash
# Add to crontab
crontab -e

# Daily backup at 3 AM
0 3 * * * tar -czvf /home/openclaw/backups/openclaw-$(date +\%F).tar.gz /home/openclaw/.openclaw

# Keep last 7 days
0 4 * * * find /home/openclaw/backups -mtime +7 -delete
```

---

## Step 7: Docker Deployment (Optional)

### Install Docker

```bash
sudo apt update
sudo apt install apt-transport-https ca-certificates curl software-properties-common -y

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list

sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
sudo usermod -aG docker openclaw
```

### Run OpenClaw in Docker

```bash
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh
docker compose up -d
```

---

## Step 8: Secure Remote Access (Recommended)

### Option A: Tailscale VPN (Recommended)

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up

# Follow authentication link
# Now access via: http://<tailscale-ip>:18789
```

### Option B: SSH Tunnel

```bash
# From local machine
ssh -i key.pem -L 18789:localhost:18789 ubuntu@EC2_IP

# Access: http://localhost:18789
```

---

## Quick Commands Reference

```bash
# Service management
sudo systemctl start openclaw
sudo systemctl stop openclaw
sudo systemctl restart openclaw
sudo systemctl status openclaw

# Logs
journalctl -u openclaw -f          # Real-time logs
journalctl -u openclaw --since "1 hour ago"

# Configuration
openclaw config list               # Show config
openclaw config set <key> <value>  # Set value
openclaw doctor                    # Diagnose issues

# Updates
sudo npm update -g openclaw
sudo systemctl restart openclaw
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `openclaw: command not found` | Add to PATH: `export PATH="$PATH:$(npm root -g)/openclaw"` |
| Node version too old | Install Node 22+: `curl -fsSL https://deb.nodesource.com/setup_22.x \| sudo -E bash -` |
| Port 18789 in use | `lsof -i :18789` or change port via config |
| Out of memory | Upgrade to t3.small or larger |
| Can't connect via SSH | Check security group, key permissions (chmod 400) |

---

## Instance Costs (ap-southeast-1)

| Instance | Hourly | Monthly (730hrs) |
|----------|--------|------------------|
| t3.micro | ~$0.0104 | ~$7.60 |
| t3.small | ~$0.0208 | ~$15.20 |
| t3.medium | ~$0.0416 | ~$30.40 |
| m7i-flex.large | ~$0.0765 | ~$55.80 |

**Tip:** Use Reserved Instances for 30-60% savings on production nodes.

---

## Agent Deployment (Layer 2)

After provisioning EC2 with Layer 1, deploy agents:

```bash
# On provisioned EC2:

# Clone deployment repo
git clone https://github.com/0x-wzw/zodiac-v3.git
cd zodiac-v3

# Run agent deployment script
./deploy-agent.sh --role february --model ollama/kimi-k2.5:cloud

# Or for multi-agent swarm:
git clone https://github.com/0x-wzw/oasis-v2.git
cd oasis-v2
./deploy-swarm.sh --nodes 12
```

**Deployment repos handle:**
- Agent configuration (persona, model, routing)
- Skill installation from ClawHub
- Memory initialization
- Channel setup (Telegram, Discord)
- Inter-agent communication config
- Workflow definitions

---

## Next Steps

1. ✅ Provision EC2 (this guide)
2. ⬜ Clone deployment repo (zodiac-v3 / oasis-v2)
3. ⬜ Run agent deployment script
4. ⬜ Verify agent spawns correctly
5. ⬜ Configure channels and integrations

---

*Version: 1.0 | For standalone EC2 deployment*
