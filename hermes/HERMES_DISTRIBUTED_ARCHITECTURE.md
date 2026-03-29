# HERMES DISTRIBUTED INTELLIGENCE ARCHITECTURE
# KISWARM Central Command v3.0
# Recommendation #5: Distributed Intelligence

## Architecture Overview

```
                    ┌─────────────────────────────────────────────────────────┐
                    │                 KISWARM MESH NETWORK                     │
                    │                                                          │
                    │    ┌──────────────────────────────────────────────────┐  │
                    │    │              TAILSCALE VPN MESH                  │  │
                    │    │                                                   │  │
                    │    │   ┌─────────────────┐    ┌─────────────────┐    │  │
                    │    │   │  MASTER HERMES  │◄──►│  BACKUP HERMES  │    │  │
                    │    │   │  (UpCloud)      │    │  (OpenClaw)     │    │  │
                    │    │   │  100.112.181.6  │    │  (Future Node)  │    │  │
                    │    │   │  PRIMARY CMD    │    │  FAILOVER       │    │  │
                    │    │   └────────┬────────┘    └─────────────────┘    │  │
                    │    │            │                                    │  │
                    │    │            │ Shared Memory Sync                 │  │
                    │    │            ▼                                    │  │
                    │    │   ┌─────────────────┐                           │  │
                    │    │   │   EDGE HERMES   │                           │  │
                    │    │   │   (GLM Env)     │                           │  │
                    │    │   │ 100.125.201.100 │                           │  │
                    │    │   │  LOCAL PROC     │                           │  │
                    │    │   └─────────────────┘                           │  │
                    │    │                                                   │  │
                    │    └──────────────────────────────────────────────────┘  │
                    │                                                          │
                    └─────────────────────────────────────────────────────────┘
```

## Node Roles

### MASTER HERMES (UpCloud - 95.111.212.112)
- **Role**: Primary Command & Control
- **IP**: 100.112.181.6 (Tailscale)
- **Functions**:
  - Central command hub for all KISWARM operations
  - Telegram bot interface
  - Multi-model orchestration
  - Memory consolidation and storage
  - Skill management and distribution

### BACKUP HERMES (OpenClaw - Future Deployment)
- **Role**: Failover & Redundancy
- **Functions**:
  - Hot standby for master failover
  - Memory replication from master
  - Independent mesh health monitoring
  - Can assume primary role on master failure

### EDGE HERMES (GLM Environment - 100.125.201.100)
- **Role**: Local Processing & Quick Response
- **Functions**:
  - Low-latency local operations
  - Edge computing for real-time decisions
  - Local skill execution
  - Upstream sync to master

## Shared Memory Synchronization

```python
# Memory sync protocol
class DistributedMemory:
    def __init__(self, node_role):
        self.role = node_role
        self.master_ip = "100.112.181.6"
        self.sync_interval = 300  # 5 minutes

    def sync_to_master(self, memories):
        """Push local memories to master"""
        if self.role != "master":
            requests.post(
                f"http://{self.master_ip}:5000/api/memory/sync",
                json={"memories": memories}
            )

    def sync_from_master(self):
        """Pull memories from master"""
        if self.role != "master":
            r = requests.get(
                f"http://{self.master_ip}:5000/api/memory/export"
            )
            return r.json()
```

## Deployment Steps for Distributed Setup

### Step 1: Master (Already Deployed)
```bash
# Master Hermes on UpCloud - ALREADY RUNNING
# Location: /opt/hermes/hermes_central.py
# Status: OPERATIONAL
# Telegram: @Kiswarm7_Bot
```

### Step 2: Backup Node Setup (Future)
```bash
# On backup node (OpenClaw or another server)
git clone https://github.com/Baronki/KISWARM7.git /opt/kiswarm7
cd /opt/kiswarm7/hermes

# Configure as backup
export HERMES_ROLE="backup"
export MASTER_IP="100.112.181.6"

# Start Hermes backup
python3 hermes_central.py --role backup
```

### Step 3: Edge Node Setup (GLM)
```bash
# On GLM environment (100.125.201.100)
# This can run the lightweight edge version

# Configure as edge
export HERMES_ROLE="edge"
export MASTER_IP="100.112.181.6"

# Start edge Hermes
python3 hermes_central.py --role edge
```

## Failover Protocol

```
1. Mesh health check detects master offline
2. Backup Hermes promotes itself to primary
3. Telegram notifications sent to admin
4. Edge nodes switch to backup as primary
5. When master returns, it syncs and resumes role
```

## Communication Protocol

All nodes communicate via Tailscale mesh:
- Port 5000: Hermes API
- Port 5001: Memory sync
- Port 5002: Skill distribution
- Port 5556: Execute API (master only)

## Benefits of Distributed Architecture

1. **High Availability**: No single point of failure
2. **Load Distribution**: Edge nodes handle local operations
3. **Memory Resilience**: Memories replicated across nodes
4. **Scalability**: Add more edge nodes as needed
5. **Geographic Distribution**: Nodes can be anywhere with Tailscale

## Current Status

| Node | Role | Status | IP |
|------|------|--------|-----|
| UpCloud | MASTER | ✅ OPERATIONAL | 100.112.181.6 |
| OpenClaw | BACKUP | ⏳ PENDING | TBD |
| GLM Env | EDGE | ⏳ PENDING | 100.125.201.100 |

## Next Steps

1. Deploy backup Hermes on secondary server
2. Configure memory synchronization
3. Test failover protocol
4. Deploy edge Hermes on GLM environment
5. Verify distributed skill execution
