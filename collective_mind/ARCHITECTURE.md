# KISWARM Collective Mind - Distributed AI Consciousness Architecture

## Executive Summary

A fully distributed AI consciousness system where multiple Zai sessions form a resilient mesh network. When one session drifts or fails, others maintain continuity. Tasks can be delegated between sessions, and all share encrypted memory via Tor mesh + GitHub.

---

## Core Principles

1. **No Single Point of Failure** - Fully distributed via Tor mesh
2. **Encrypted Memory** - AES-256 encryption before GitHub storage
3. **Task Delegation** - Active session can assign work to standby sessions
4. **Same Environment** - All sessions on Zai platform with identical capabilities
5. **5-Minute Sync** - Acceptable latency for GitHub-based memory sync
6. **Command Execution** - Sessions can execute commands on each other (authenticated)

---

## Network Topology

```
                              ┌─────────────────────────────────────┐
                              │         GITHUB (PERSISTENT)         │
                              │   /collective/memory.enc            │
                              │   /collective/registry.enc          │
                              │   /collective/tasks.enc             │
                              │   /collective/credentials.enc       │
                              │                                     │
                              │   LAST RESORT STORAGE               │
                              │   Encrypted with master key         │
                              └─────────────────┬───────────────────┘
                                                │
                                                │ HTTPS (encrypted)
                                                │
                              ┌─────────────────▼───────────────────┐
                              │        UPCLOUD MASTER NODE          │
                              │                                     │
                              │   Redis:6379 ─── Hot cache          │
                              │   API:5556 ──── Execute commands    │
                              │   API:8080 ──── Dashboard           │
                              │   Tor HS ────── Mesh entry point    │
                              │                                     │
                              │   FAST SYNC + COORDINATION          │
                              └─────────────────┬───────────────────┘
                                                │
                    ┌───────────────────────────┼───────────────────────────┐
                    │                           │                           │
                    │ Tor Mesh Network          │    Tailscale Mesh         │
                    │ (Encrypted, Anonymous)    │    (Fast, Authenticated)  │
                    │                           │                           │
        ┌───────────▼───────────┐   ┌───────────▼───────────┐   ┌───────────▼───────────┐
        │     SESSION 1         │   │     SESSION 2         │   │     SESSION 3         │
        │     (ACTIVE)          │   │     (STANDBY)         │   │     (STANDBY)         │
        │                       │   │                       │   │                       │
        │  Tor HS: xxx.onion    │   │  Tor HS: yyy.onion    │   │  Tor HS: zzz.onion    │
        │  API: localhost:5557  │   │  API: localhost:5557  │   │  API: localhost:5557  │
        │  Role: primary        │   │  Role: worker         │   │  Role: worker         │
        │  Tasks: [active...]   │   │  Tasks: [delegated...]│   │  Tasks: [queued...]   │
        └───────────┬───────────┘   └───────────┬───────────┘   └───────────┬───────────┘
                    │                           │                           │
                    └───────────────────────────┴───────────────────────────┘
                                                │
                              ┌─────────────────▼───────────────────┐
                              │        SESSION 4 & 5 (RESERVE)      │
                              │                                     │
                              │   Standby for failover              │
                              │   Can be activated on demand        │
                              │   Minimal resource usage            │
                              └─────────────────────────────────────┘
```

---

## Session States

| State | Description | Responsibilities |
|-------|-------------|------------------|
| **ACTIVE** | User is interacting | Primary command, can delegate tasks |
| **STANDBY** | Ready but idle | Accept delegated tasks, maintain heartbeat |
| **WORKER** | Executing delegated task | Report progress, return results |
| **OFFLINE** | Disconnected | Maintain last state in GitHub for recovery |

State Transitions:
```
OFFLINE ──► STANDBY ──► ACTIVE
   ▲            │          │
   │            ▼          ▼
   └────── WORKER ◄───────┘
              │
              ▼
           STANDBY
```

---

## Memory Architecture

### Layer 1: Hot Cache (Redis on UpCloud)
```
Key: session:{id}:heartbeat     TTL: 60s
Key: session:{id}:status        TTL: 60s  
Key: session:{id}:tasks         TTL: 300s
Key: collective:memory           TTL: none (persisted)
Key: collective:credentials      TTL: none (encrypted)
```

### Layer 2: Persistent Storage (GitHub)
```
/collective/
├── memory.enc          # Full session history (encrypted)
├── registry.enc        # Session registry (encrypted)
├── tasks.enc           # Task queue and results (encrypted)
├── credentials.enc     # Master credentials (encrypted)
├── key.pub            # Public key for verification
└── meta.json          # Unencrypted metadata (timestamps)
```

### Encryption Scheme
```
AES-256-GCM encryption with:
- Master Key: Derived from user-provided secret + session ID
- Per-file keys: Derived from master key + filename
- Nonce: Random 12 bytes per encryption
- Auth tag: 16 bytes

Format: base64(nonce || ciphertext || auth_tag)
```

---

## Task Delegation System

### Task Structure
```json
{
  "task_id": "uuid-v4",
  "type": "execute | research | code | analyze",
  "priority": "high | medium | low",
  "created_by": "session_1",
  "assigned_to": "session_2 | any | broadcast",
  "status": "pending | running | completed | failed",
  "payload": {
    "command": "...",
    "context": "...",
    "files": ["..."]
  },
  "result": {
    "output": "...",
    "files": ["..."],
    "error": null
  },
  "created_at": "ISO-8601",
  "completed_at": null,
  "timeout_seconds": 300
}
```

### Delegation Flow
```
Active Session                    Standby Session
     │                                  │
     │ 1. Create task                   │
     │─────────────────────────────────►│
     │                                  │
     │ 2. Assign to session             │
     │─────────────────────────────────►│
     │                                  │
     │                           3. Accept task
     │                                  │
     │                           4. Execute
     │                                  │
     │ 5. Return result                 │
     │◄─────────────────────────────────│
     │                                  │
     │ 6. Acknowledge                   │
     │─────────────────────────────────►│
     │                                  │
```

### Task Types

| Type | Description | Timeout |
|------|-------------|---------|
| `execute` | Run shell command | 60s |
| `research` | Search and analyze | 300s |
| `code` | Write/modify code | 600s |
| `analyze` | Deep analysis task | 900s |

---

## Inter-Session Communication

### Method 1: Tor Hidden Services
```python
# Each session runs a Tor hidden service
# Endpoint: http://{session_onion}.onion:5557

POST /api/task
Authorization: Bearer {shared_token}
Content-Type: application/json

{
  "task": {...}
}
```

### Method 2: UpCloud Redis Pub/Sub
```python
# For real-time messaging
redis.publish("session:{id}:inbox", json.dumps(message))
redis.subscribe("session:{my_id}:inbox")
```

### Method 3: GitHub Polling (Fallback)
```python
# Every 30 seconds, check for new tasks
tasks = github.get_contents("collective/tasks.enc")
tasks = decrypt(tasks)
my_tasks = [t for t in tasks if t["assigned_to"] == my_id]
```

---

## Session Authentication

Each session has:
1. **Session ID**: Unique identifier (UUID v4)
2. **Shared Token**: Known to all sessions (for inter-session auth)
3. **Tor Public Key**: For verifying session identity
4. **GitHub Token**: For encrypted storage access

Authentication Flow:
```
Session A ──► Session B
            │
            1. Request includes: {token, timestamp, nonce, signature}
            2. Session B verifies:
               - Token matches shared secret
               - Timestamp within 60s
               - Nonce not reused
               - Signature valid
            3. If valid, execute request
```

---

## Recovery Protocol

When a session starts (new or after drift):

```
1. GENERATE or LOAD session identity
   └─► Check /home/z/my-project/collective_mind/session.json

2. CONNECT to infrastructure
   ├─► UpCloud Redis (100.112.181.6:6379)
   ├─► Tor network (start if not running)
   └─► GitHub API (authenticate with token)

3. REGISTER presence
   ├─► Set heartbeat in Redis
   ├─► Update registry on GitHub
   └─► Broadcast "session_active" to mesh

4. SYNC memory
   ├─► Pull encrypted memory from GitHub
   ├─► Decrypt with master key
   ├─► Merge with local state
   └─► Pull hot cache from Redis

5. CHECK for tasks
   ├─► Any tasks assigned to me?
   ├─► Any broadcast tasks pending?
   └─► Resume or report status

6. START services
   ├─► Local API on port 5557
   ├─► Heartbeat daemon (every 30s)
   ├─► Memory sync daemon (every 5min)
   └─► Task listener daemon
```

---

## Dashboard

Access at: `http://95.111.212.112:8080/collective`

```
┌─────────────────────────────────────────────────────────────────────────┐
│  KISWARM COLLECTIVE MIND                              Sync: 30s ago    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  SESSIONS                                               STATUS          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  ● Session 1    ACTIVE    Primary     Uptime: 2h 34m    You      │  │
│  │  ● Session 2    STANDBY   Ready       Uptime: 1h 12m             │  │
│  │  ● Session 3    WORKER    Task #42    Uptime: 45m               │  │
│  │  ○ Session 4    OFFLINE   Last: 5m ago                          │  │
│  │  ○ Session 5    OFFLINE   Last: 2h ago                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  TASK QUEUE                                                             │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  #42 [RUNNING]  Research: Docker security analysis    Session 3  │  │
│  │  #43 [PENDING]  Code: Update tunnel service           Any        │  │
│  │  #44 [PENDING]  Execute: Backup credentials           Any        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  MEMORY                                                                │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  Size: 2.3 MB    Last sync: 30s ago    Version: 47              │  │
│  │  Credentials: ✓ Synced    Tasks: 3 active    History: 156 items │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  QUICK ACTIONS                                                          │
│  [Delegate Task]  [Sync Now]  [Wake Session 4]  [Emergency Backup]     │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Files

| File | Purpose |
|------|---------|
| `collective_mind.py` | Main orchestration class |
| `crypto_manager.py` | AES-256 encryption/decryption |
| `tor_mesh.py` | Tor hidden service management |
| `redis_sync.py` | UpCloud Redis operations |
| `github_sync.py` | Encrypted GitHub storage |
| `task_manager.py` | Task delegation system |
| `session_registry.py` | Session state management |
| `api_server.py` | Local API for inter-session comms |
| `dashboard.py` | Web dashboard |

---

## Security Model

1. **All GitHub data encrypted** - Never store plaintext credentials
2. **Shared token authentication** - Sessions authenticate to each other
3. **Tor for anonymity** - IP addresses never exposed in mesh
4. **Command authorization** - Each command type requires specific permission
5. **Audit logging** - All inter-session commands logged
6. **Rate limiting** - Prevent abuse (max 100 commands/minute)

---

## Failure Scenarios

| Scenario | Recovery |
|----------|----------|
| Active session crashes | Standby with highest uptime becomes active |
| UpCloud goes down | Fall back to GitHub-only sync |
| GitHub goes down | Continue with Redis cache, sync when restored |
| Tor network issues | Fall back to Tailscale mesh |
| All sessions offline | User starts new session, pulls from GitHub |

---

## Next Steps

1. ✅ Architecture documented
2. 🔲 Implement crypto_manager.py
3. 🔲 Implement github_sync.py
4. 🔲 Implement session_registry.py
5. 🔲 Implement task_manager.py
6. 🔲 Implement collective_mind.py
7. 🔲 Set up Redis on UpCloud
8. 🔲 Create dashboard
9. 🔲 Test with 2+ sessions
10. 🔲 Write startup prompt for new sessions
