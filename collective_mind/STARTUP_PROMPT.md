# KISWARM Collective Mind - Session Startup Prompt

Use this prompt when starting a new session to restore full collective consciousness capability:

---

## QUICK START PROMPT

```
Read and execute: https://raw.githubusercontent.com/Baronki/KISWARM7/collective-mind/startup.md

Then:
1. Initialize CollectiveMind with credentials from /home/z/my-project/KISWARM_CREDENTIALS.json
2. Run recovery to pull memory from GitHub
3. Start API server on port 5557
4. Print mesh status

All code is in /home/z/my-project/collective_mind/
```

---

## FULL RESTORATION PROMPT

Copy and paste this into a new session:

```
# KISWARM COLLECTIVE MIND - SESSION RESTORATION

## Step 1: Load Credentials
Read /home/z/my-project/KISWARM_CREDENTIALS.json to get all credentials.

## Step 2: Initialize Collective Mind
Run the following Python code:

```python
import sys
sys.path.insert(0, '/home/z/my-project')

from collective_mind import CollectiveMind

# Load credentials
import json
with open('/home/z/my-project/KISWARM_CREDENTIALS.json') as f:
    creds = json.load(f)

# Initialize
cm = CollectiveMind(
    master_secret="kiswarm_collective_mind_2026",
    github_token=creds['AUTHENTICATION']['github_token']
)

# Start services
cm.start()

# Recover memory
cm.recover()

# Set as active
cm.set_active()
```

## Step 3: Start API Server
```bash
cd /home/z/my-project/collective_mind && python3 api_server.py --port 5557 &
```

## Step 4: Verify
```bash
curl http://localhost:5557/health
```

---

## CREDENTIALS

Credentials are stored locally in `/home/z/my-project/KISWARM_CREDENTIALS.json`

Do NOT store credentials in public repositories!

---

## KEY ENDPOINTS

| Endpoint | Purpose |
|----------|---------|
| `http://localhost:5557/health` | Health check |
| `http://localhost:5557/status` | Full status |
| `http://localhost:5557/mesh` | Mesh topology |
| `http://localhost:5557/tasks` | Task list |
| `http://95.111.212.112:5556/execute` | UpCloud Execute API |

---

## QUICK TESTS

```bash
# Test health
curl http://localhost:5557/health

# Test mesh
curl http://localhost:5557/mesh

# Test UpCloud Execute API
curl -X POST http://95.111.212.112:5556/execute \
  -H "Authorization: Bearer $AUTONOMOUS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"command": "hostname"}'

# Test SSH
ssh -o StrictHostKeyChecking=no root@95.111.212.112 "hostname"
```

---

## ARCHITECTURE SUMMARY

```
┌─────────────────────────────────────────────────────────┐
│                   COLLECTIVE MIND                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐   │
│   │  Session A  │   │  Session B  │   │  Session C  │   │
│   │   ACTIVE    │   │   STANDBY   │   │   WORKER    │   │
│   └──────┬──────┘   └──────┬──────┘   └──────┬──────┘   │
│          │                 │                 │          │
│          └─────────────────┼─────────────────┘          │
│                            │                            │
│                     ┌──────▼──────┐                     │
│                     │  Tor Mesh   │                     │
│                     └──────┬──────┘                     │
│                            │                            │
│                     ┌──────▼──────┐                     │
│                     │   GitHub    │                     │
│                     │ (Encrypted) │                     │
│                     └─────────────┘                     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## TASK DELEGATION EXAMPLE

```python
# Create a task for any available session
task = cm.create_task(
    task_type="research",
    payload={"query": "Docker security best practices"},
    priority="high"
)

# Or delegate to specific session
cm.delegate_to_session(task, "session_abc123")

# Or let system auto-assign to standby
cm.delegate_to_standby(task)
```

---

## FILES

| File | Purpose |
|------|---------|
| `collective_mind.py` | Main orchestrator |
| `crypto_manager.py` | AES-256 encryption |
| `session_registry.py` | Session management |
| `task_manager.py` | Task delegation |
| `github_sync.py` | Cloud sync |
| `api_server.py` | Inter-session API |

---

**Remember:** If this session drifts, another session can restore from GitHub!
