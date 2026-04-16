# OpenClaw Deployment Guide — Swarm Architecture

**Comprehensive guide for deploying OpenClaw across 12 EC2 instances (January–December)**

---

## Current Setup Analysis

### What We Have
- **Primary:** EC2 instance running OpenClaw on port 18789
- **Channel:** Kimi-claw (current interface)
- **Models:** Ollama Cloud (free via Pro)
- **Architecture:** Centralized hub (October) + specialized colonies

### What We Need
- **12 EC2 instances** for full swarm deployment
- **Full autonomous deployment** (no manual setup per instance)
- **Cross-instance communication** and knowledge sharing
- **Headless operation** (no TUI required)

---

## Deployment Methods

### Method 1: Ollama Launch (Recommended for Single Instance)

```bash
# Quick deployment
ollama launch openclaw --model kimi-k2.5:cloud --yes

# Headless mode for servers
ollama launch openclaw --model kimi-k2.5:cloud --yes --headless

# Non-interactive with specific config
ollama launch openclaw --config --model minimax-m2.7:cloud
```

**Pros:** Fast, automated, recommended by Ollama
**Cons:** Requires Ollama CLI on each instance

---

### Method 2: Direct Installation (For Custom Setups)

```bash
# Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# Configure for Kimi API
openclaw configure --section model
# Select: Moonshot AI → Kimi API Key

# Configure channels
openclaw configure --section channels
```

**Pros:** Full control, works without Ollama CLI
**Cons:** Manual configuration needed

---

### Method 3: Docker (For Containerized Deployment)

```dockerfile
FROM node:20-alpine

RUN npm install -g openclaw

EXPOSE 18789

CMD ["openclaw", "gateway", "--port", "18789"]
```

```bash
# Run container
docker run -d \
  --name openclaw \
  -p 18789:18789 \
  -v ~/.openclaw:/root/.openclaw \
  openclaw:latest
```

**Pros:** Isolated, reproducible, scalable
**Cons:** Additional container overhead

---

### Method 4: Headless/API-Only (For Swarm Nodes)

```bash
# Start gateway in headless mode
openclaw gateway start \
  --model kimi-k2.5:cloud \
  --port 18789 \
  --headless \
  --api-key ${KIMI_API_KEY}

# API-only mode (no TUI, no chat interface)
openclaw gateway start \
  --model minimax-m2.7:cloud \
  --api-only
```

**Pros:** Minimal resource usage, perfect for swarm nodes
**Cons:** No interactive chat capability

---

---

## Additional Deployment Methods (From External Research)

### Method 5: Docker + Tailscale (Recommended for Security)

**Source:** [Remote OpenClaw Blog](https://remoteopenclaw.com/blog/openclaw-aws-docker-tailscale/)

The secure approach: Run OpenClaw in Docker with Tailscale VPN for private network access. **No public ports exposed.**

```bash
# 1. Harden SSH (non-standard port 2222, key-only)
ssh -i "your-key.pem" ubuntu@<EC2-IP>
sudo adduser openclaw
sudo usermod -aG sudo openclaw

# 2. Copy SSH keys to new user
sudo mkdir -p /home/openclaw/.ssh
sudo cp /home/ubuntu/.ssh/authorized_keys /home/openclaw/.ssh/
sudo chown -R openclaw:openclaw /home/openclaw/.ssh

# 3. Configure firewall (UFW + AWS SG)
sudo ufw default deny incoming
sudo ufw allow 2222/tcp
sudo ufw enable

# 4. Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list
sudo apt update && sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin -y
sudo usermod -aG docker openclaw

# 5. Install Tailscale (free tier works)
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up  # Follow auth link

# 6. Clone and run OpenClaw
git clone https://github.com/openclaw/openclaw.git
cd openclaw
./docker-setup.sh

# Select: Manual setup → Local gateway → Anthropic API → Tailnet bind → Token auth

# 7. Access via Tailscale IP (no public ports!)
# Get your tailnet IP: tailscale ip -4
# Access: http://<TAILSCALE-IP>:18789
```

**Security Benefits:**
- Zero public application ports
- Tailscale encrypts all traffic end-to-end
- Non-standard SSH port (2222)
- Dual-layer firewall (UFW + AWS SG)
- Docker isolation

**Cost:** ~$8-15/month for t3.small + Tailscale free tier

---

### Method 6: Terraform + AWS Bedrock (IaC Approach)

**Source:** [GitHub aws-samples/sample-OpenClaw-on-AWS-with-Bedrock](https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock)

Infrastructure as Code using Terraform with Amazon Bedrock for LLM.

```bash
# Clone the Terraform template
git clone https://github.com/aws-samples/sample-OpenClaw-on-AWS-with-Bedrock.git
cd sample-OpenClaw-on-AWS-with-Bedrock

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var="instance_type=t3.medium" -var="region=ap-southeast-1"

# Apply (creates VPC, EC2, Security Groups, OpenClaw)
terraform apply -var="instance_type=t3.medium" -var="region=ap-southeast-1" -var="bedrock_region=us-east-1"

# Get outputs
terraform output
```

**What's Deployed:**
- VPC with public subnet
- EC2 instance (configurable size)
- Security group (SSH + OpenClaw port)
- IAM role with Bedrock access
- OpenClaw installed + configured

**Terraform Variables:**
```hcl
instance_type = "t3.medium"  # or m7i-flex.large for better performance
region = "ap-southeast-1"
bedrock_region = "us-east-1"
openclaw_version = "latest"
```

---

### Method 7: Hardened Ubuntu (Systemd Service)

**Source:** [OpenClaw Roadmap](https://openclawroadmap.com/install-vps-aws.php)

Full systemd service setup for 24/7 operation.

```bash
# Install Node.js 22+
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt-get install -y nodejs

# Install OpenClaw
curl -fsSL https://openclaw.ai/install.sh | bash

# Run setup wizard
openclaw setup
# Select: LLM provider → API key → First channel (optional)

# Install systemd service (keeps OpenClaw running 24/7)
sudo openclaw service install --systemd
sudo systemctl enable openclaw
sudo systemctl start openclaw

# Verify
sudo systemctl status openclaw
openclaw status

# View logs
journalctl -u openclaw -f
```

**Instance Sizing:**
| Use Case | Instance | RAM | Cost/mo |
|----------|---------|-----|---------|
| Free tier trial | t3.micro | 1 GB | ~$0 (12mo) |
| Light use | t3.small | 2 GB | ~$8-15 |
| Production | t3.medium | 4 GB | ~$15-20 |
| **Swarm nodes** | **m7i-flex.large** | **8 GB** | ~$25-30 |

---

## Deployment Method Comparison

| Method | Security | Complexity | Cost | Best For |
|--------|----------|------------|------|----------|
| **Docker + Tailscale** | ⭐⭐⭐⭐⭐ | Medium | $8-15/mo | Production, high security |
| **Terraform + Bedrock** | ⭐⭐⭐⭐ | High (IaC) | $15-25/mo | IaC teams, repeatable deploys |
| **Systemd Service** | ⭐⭐⭐ | Low | $8-20/mo | Simple 24/7 operation |
| **Ollama Launch** | ⭐⭐⭐ | Low | $8-15/mo | Quick testing |
| **Headless/API** | ⭐⭐⭐ | Low | $8-15/mo | Swarm nodes |
| **Docker only** | ⭐⭐ | Low | $8-15/mo | Containerized infra |

---

## Security Best Practices (From External Research)

1. **Never expose gateway port to internet** — bind to 127.0.0.1 or use Tailscale
2. **Use SSH key-only authentication** — disable password auth
3. **Non-standard SSH port** — change from 22 to 2222
4. **Dual-layer firewall** — AWS SG + UFW on host
5. **Run as dedicated user** — not root (principle of least privilege)
6. **Set API spend limits** — prevent runaway costs ($20-30/month hard limit)
7. **Regular backups** — tar + cron for memory files
8. **Docker socket protection** — add user to docker group only if needed

---

## Swarm Deployment: 12-Instance Architecture

### Instance Roles

| Instance | Role | OpenClaw Config | Specialization |
|----------|-------|-----------------|----------------|
| January | Commander | Full + TUI | Orchestration |
| February | Operations | Full + TUI | Scheduling |
| March | Infrastructure | Headless/API | DevOps |
| April | Memory | Headless/API | Knowledge |
| May | Research | Full + TUI | Analysis |
| June | Code | Full + TUI | Development |
| July | Content | Headless/API | Creation |
| August | Analytics | Headless/API | Data |
| September | Quality | Headless/API | Validation |
| October | Interface | Full + TUI | **Hub (current)** |
| November | Strategy | Full + TUI | Planning |
| December | Trading | Headless/API | Finance |

---

## Autonomous Deployment Script

### Bootstrap Script for New EC2 Instance

```bash
#!/bin/bash
# openclaw-swarm-node.sh
# Deploy OpenClaw as headless swarm node

set -e

# Configuration
INSTANCE_NAME=${1:-"node"}
INSTANCE_ROLE=${2:-"worker"}
MODEL=${3:-"minimax-m2.7:cloud"}
API_KEY=${KIMI_API_KEY:-""}

echo "=== OpenClaw Swarm Node Deployment ==="
echo "Instance: $INSTANCE_NAME"
echo "Role: $INSTANCE_ROLE"
echo "Model: $MODEL"

# 1. Install OpenClaw
echo "[1/6] Installing OpenClaw..."
curl -fsSL https://openclaw.ai/install.sh | bash

# 2. Configure API key
echo "[2/6] Configuring API..."
openclaw configure --section model << EOF
moonshot
api-key
$API_KEY
$MODEL
EOF

# 3. Configure headless mode
echo "[3/6] Enabling headless mode..."
openclaw configure --section gateway << EOF
headless
true
port
18789
EOF

# 4. Register with swarm
echo "[4/6] Registering with swarm hub..."
openclaw swarm register \
  --hub ${SWARM_HUB_URL:-"http://october:18789"} \
  --name $INSTANCE_NAME \
  --role $INSTANCE_ROLE

# 5. Configure knowledge sync
echo "[5/6] Setting up knowledge sync..."
openclaw knowledge sync enable \
  --hub ${SWARM_HUB_URL:-"http://october:18789"} \
  --interval 60

# 6. Start gateway
echo "[6/6] Starting gateway..."
openclaw gateway start --headless

echo "=== Deployment Complete ==="
echo "Node: $INSTANCE_NAME"
echo "API: http://localhost:18789"
echo "Swarm: registered"
```

### Deployment Command

```bash
# Deploy new swarm node
./openclaw-swarm-node.sh january commander minimax-m2.7:cloud
./openclaw-swarm-node.sh february operations glm-4.7:cloud
./openclaw-swarm-node.sh march infra ministral-3:8b-cloud
# ... etc
```

---

## Cross-Instance Communication

### Relay Server (Current: Port 18790)

```bash
# Current setup - intra-instance communication
curl -X POST http://localhost:18790/relay \
  -H "Authorization: Bearer agent-relay-secret-2026" \
  -d '{"to": "halloween", "message": "task complete"}'
```

### Swarm API (For Inter-Instance)

```bash
# Query another node
curl http://<node-ip>:18789/api/query \
  -H "X-Swarm-Key: ${SWARM_SHARED_KEY}" \
  -d '{"task": "research", "context": "..."}'

# Delegate task
curl -X POST http://<node-ip>:18789/api/delegate \
  -H "X-Swarm-Key: ${SWARM_SHARED_KEY}" \
  -d '{"task_id": "123", "task": "...", "callback": "http://october:18789/callback"}'
```

---

## Knowledge Sync Configuration

### Hub (October) Configuration

```json
{
  "knowledge_hub": {
    "enabled": true,
    "port": 18789,
    "sync_protocol": "bidirectional",
    "push_on_change": true,
    "pull_interval_seconds": 60
  }
}
```

### Node Configuration

```json
{
  "knowledge_node": {
    "enabled": true,
    "hub_url": "http://october:18789",
    "sync_direction": "push_and_pull",
    "local_cache_ttl_hours": 24
  }
}
```

---

## Deployment Checklist

### Pre-Deployment
- [ ] EC2 instances provisioned (12x)
- [ ] Security groups configured (ports 18789, 18790)
- [ ] API keys distributed (via secrets manager)
- [ ] Swarm shared key generated

### Per-Instance Deployment
- [ ] SSH access verified
- [ ] OpenClaw installed
- [ ] Model configured
- [ ] Headless mode enabled
- [ ] Swarm registration complete
- [ ] Knowledge sync configured
- [ ] Health check passed

### Post-Deployment
- [ ] Inter-node communication verified
- [ ] Knowledge propagation tested
- [ ] Task delegation tested
- [ ] Failover simulation passed

---

## Failover & Scaling

### Adding New Node

```bash
# Quick scale - clone configuration
./openclaw-swarm-node.sh new-node worker minimax-m2.7:cloud

# Register with existing swarm
openclaw swarm rebalance
```

### Failover Configuration

```bash
# Set backup hub
openclaw swarm configure --backup-hub http://backup:18789

# Enable automatic failover
openclaw swarm failover enable
```

---

## Monitoring & Health

### Swarm Status

```bash
# Check all nodes
openclaw swarm status

# Node health
openclaw gateway health --node <node-name>

# Knowledge sync status
openclaw knowledge status
```

### Logs

```bash
# View node logs
openclaw logs --node <node-name> --tail 100

# Swarm events
openclaw logs --filter swarm --since 1h
```

---

## Future Deployment Options

### Kubernetes Deployment
- Helm chart for OpenClaw
- Auto-scaling based on task queue
- Service mesh for inter-node communication

### Terraform/Ansible Templates
- Infrastructure as code
- Reproducible deployments
- Variable-based configuration

### Managed Services
- OpenClaw Cloud (future)
- Kimi Platform hosting
- Ollama Cloud managed

---

## Reference Links

- [OpenClaw Docs](https://docs.ollama.com/integrations/openclaw)
- [Kimi Platform](https://platform.kimi.ai)
- [Ollama Cloud](https://ollama.com/cloud)
- [ClawHub Skills](https://clawhub.ai)

---

*Deployment Guide Version: 1.0 | For 12-EC2 Swarm Architecture*
