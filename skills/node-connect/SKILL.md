---
name: node-connect
description: Diagnose OpenClaw node connection and pairing failures for Android, iOS, and macOS companion apps. Use when QR/setup code/manual connect fails, local Wi-Fi works but VPS/tailnet does not, or errors mention pairing required, unauthorized, bootstrap token invalid or expired, gateway.bind, gateway.remote.url, Tailscale, or plugins.entries.device-pair.config.publicUrl.
---

# Node Connect Skill

Diagnose and fix device pairing issues for OpenClaw companion apps.

## Common Issues

| Error | Likely Cause | Fix |
|-------|-------------|-----|
| "Pairing required" | Device not paired | Run pairing flow |
| "Bootstrap token invalid" | Token expired | Re-generate token |
| "gateway.bind" errors | Bind address wrong | Check config |
| Works on Wi-Fi, not VPS | Firewall/port on VPS | Open port |

## Diagnostic Steps

### 1. Check Gateway Status

```bash
openclaw gateway status
```

### 2. Test Local Connectivity

```bash
curl http://localhost:18789/health
```

### 3. Check Config

```bash
openclaw gateway config show
```

### 4. Check Remote URL

For VPS deployments, ensure `gateway.remote.url` is set:
```bash
openclaw gateway config set gateway.remote.url "https://your-vps.example.com"
```

### 5. Tailscale Issues

If using Tailscale:
```bash
# Check Tailscale status
tailscale status

# Check if gateway listens on Tailscale IP
ss -tulpn | grep 18789
```

## Pairing Flow

```bash
# Generate pairing token
openclaw pairing generate

# Or via QR code
openclaw pairing qr
```

## Common Fixes

### Fix: Token Expired

```bash
openclaw pairing regenerate --device <device-id>
```

### Fix: Wrong Bind Address

In `~/.openclaw/openclaw.json`:
```json
{
  "gateway": {
    "bind": "0.0.0.0",
    "port": 18789
  }
}
```

### Fix: VPS Port Not Open

```bash
# Check if port is listening
sudo ss -tulpn | grep 18789

# Open in firewall
sudo ufw allow 18789/tcp
```

## Reference

See the full troubleshooting guide in the skill's `references/` directory or run:
```bash
openclaw help gateway
```
