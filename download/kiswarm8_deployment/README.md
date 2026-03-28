# KISWARM8.0 Deployment Package

## Overview

This deployment package contains all components needed to bring the KISWARM8.0 system to full operational status with the following features:

1. **HexStrike Agents** - Security and reconnaissance agents with health endpoints
2. **Auto-Context Restoration** - Session persistence across restarts
3. **Enhanced Dashboard APIs** - File management, GLM communication, missions view

## Files Included

| File | Purpose |
|------|---------|
| `hexstrike_agents_service.py` | Multi-agent security service (ports 5009-5017) |
| `auto_context_restoration.py` | Automatic context restoration system |
| `deploy_kiswarm8.sh` | Main deployment script |
| `dashboard_api_enhanced.ts` | Enhanced dashboard API routes |

## Quick Deployment

### On UpCloud Server (95.111.212.112)

```bash
# 1. Copy files to server
scp -r kiswarm8_deployment root@95.111.212.112:/opt/kiswarm8/

# 2. SSH to server
ssh root@95.111.212.112

# 3. Run deployment
cd /opt/kiswarm8
chmod +x deploy_kiswarm8.sh
./deploy_kiswarm8.sh --all
```

### Individual Components

```bash
# Deploy only HexStrike agents
./deploy_kiswarm8.sh --hexstrike

# Deploy only context restoration
./deploy_kiswarm8.sh --context

# Check status
./deploy_kiswarm8.sh --status
```

## HexStrike Agents

### Agent Ports and Capabilities

| Port | Agent Name | Capabilities |
|------|------------|--------------|
| 5009 | Host Discovery | Network host detection, ARP scanning, ping sweep |
| 5010 | Port Scanner | TCP/UDP scanning, service detection, banner grabbing |
| 5011 | Web Analyzer | Web app analysis, vulnerability scanning, directory enumeration |
| 5012 | Exploit Framework | Vulnerability testing, exploit execution, payload generation |
| 5013 | Stealth Recon | Passive reconnaissance, OSINT, covert operations |
| 5014 | OSINT Agent | Open source intelligence, social media analysis |
| 5015 | AI Analyzer | AI system detection, model fingerprinting |
| 5016 | Network Mapper | Topology mapping, traffic analysis |
| 5017 | Skill Acquisition | Autonomous learning, capability expansion |

### API Endpoints

Each agent provides:

```
GET  /              - Agent info
GET  /health        - Health status
GET  /status        - Detailed status
GET  /capabilities  - List capabilities
POST /execute       - Execute task (requires X-Auth-Token)
POST /scan          - Perform scan (requires X-Auth-Token)
```

### Authentication

All POST requests require the `X-Auth-Token` header:
```
X-Auth-Token: ada6952188dce59c207b9a61183e8004
```

## Auto-Context Restoration

The auto-context restoration system reads from:

1. `KISWARM_KNOWLEDGE_BASE.md` - Main knowledge reference
2. `KISWARM_CREDENTIALS.json` - Credentials and config
3. `worklog.md` - Recent task history
4. `truth_anchors.json` - Truth anchor data

### Usage

```python
from auto_context_restoration import AutoContextRestoration

restorer = AutoContextRestoration()
context = restorer.restore_all()
print(restorer.get_summary())
```

## Enhanced Dashboard APIs

### HexStrike Status

```typescript
GET /api/hexstrike/status
// Returns status of all agents
```

### File Management

```typescript
GET /api/files?dir=/path
POST /api/files/upload (multipart/form-data)
```

### GLM Communication

```typescript
GET /api/glm/status
POST /api/glm/message { "message": "...", "context": {} }
```

### Missions

```typescript
GET /api/missions
POST /api/missions { "name": "...", "description": "..." }
PUT /api/missions { "id": "...", "status": "active", "progress": 50 }
```

## Health Check

After deployment, run the health check:

```bash
/opt/kiswarm8/health_check.sh
```

Expected output:
```
=== KISWARM8.0 Health Check ===
[✓] Dashboard (8080): OPERATIONAL
[✓] Execute API (5556): OPERATIONAL
[✓] Ollama (11434): OPERATIONAL

=== HexStrike Agents ===
[✓] Agent on 5009: UP
[✓] Agent on 5010: UP
...
```

## Troubleshooting

### HexStrike agents not starting

1. Check logs: `journalctl -u hexstrike-agents -f`
2. Verify ports are free: `netstat -tlnp | grep 500`
3. Manual start: `python3 /opt/kiswarm8/services/hexstrike_agents_service.py --all`

### Dashboard timeout

1. Check model response time
2. Increase timeout in dashboard code
3. Verify Ollama is running: `curl http://localhost:11434/api/tags`

### Tailscale disconnection

1. Check status: `tailscale status`
2. Reconnect: `tailscale up`
3. Use userspace mode: `tailscaled --tun=userspace-networking`

## Credentials

All credentials are stored in `KISWARM_CREDENTIALS.json`:

```json
{
  "authentication": {
    "github_token": "ghp_...",
    "autonomous_token": "ada695...",
    "tailscale_auth_key": "tskey-auth-..."
  }
}
```

## Network Topology

```
┌─────────────────────────────────────────┐
│           INTERNET                       │
└────────────────┬────────────────────────┘
                 │
         ┌───────▼───────┐
         │  UpCloud      │ 95.111.212.112
         │  Server       │
         │               │
         │ ┌───────────┐ │
         │ │ Dashboard │ │ :8080
         │ ├───────────┤ │
         │ │ Execute   │ │ :5556
         │ │ API       │ │
         │ ├───────────┤ │
         │ │ Ollama    │ │ :11434
         │ ├───────────┤ │
         │ │ HexStrike │ │ :5009-5017
         │ │ Agents    │ │
         │ └───────────┘ │
         └───────┬───────┘
                 │ Tailscale
         ┌───────▼───────┐
         │  GLM Env      │ 100.125.201.100
         │  (Twin)       │ :5199
         └───────────────┘
```

## Support

For issues or questions, refer to:
- Knowledge Base: `/home/z/my-project/KISWARM_KNOWLEDGE_BASE.md`
- Worklog: `/home/z/my-project/worklog.md`
- Credentials: `/home/z/my-project/KISWARM_CREDENTIALS.json`
