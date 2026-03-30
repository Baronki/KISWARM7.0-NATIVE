# KISWARM Collective Mind - Quick Startup

## Immediate Restoration

Run this in a new session:

```bash
# 1. Pull collective-mind branch
cd /home/z/my-project
git fetch origin
git checkout collective-mind

# 2. Install dependencies
pip install cryptography flask requests

# 3. Initialize
python3 -c "
import sys
sys.path.insert(0, '/home/z/my-project')
from collective_mind import CollectiveMind
import json

with open('/home/z/my-project/KISWARM_CREDENTIALS.json') as f:
    creds = json.load(f)

cm = CollectiveMind(
    master_secret='kiswarm_collective_mind_2026',
    github_token=creds['AUTHENTICATION']['github_token']
)
cm.start()
cm.recover()
cm.set_active()
print('Session ID:', cm.session.session_id)
"

# 4. Start API server
python3 /home/z/my-project/collective_mind/api_server.py --port 5557 &

# 5. Verify
curl http://localhost:5557/health
```

## Credentials Location

All credentials stored locally in: `/home/z/my-project/KISWARM_CREDENTIALS.json`

**Never commit credentials to GitHub!**

## Key Endpoints

| Service | Endpoint |
|---------|----------|
| Local API | http://localhost:5557 |
| Execute API | http://95.111.212.112:5556 |
| SSH | root@95.111.212.112:22 |

## Architecture

```
Session A (Active) ◄──► Session B (Standby) ◄──► Session C (Worker)
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                          GitHub (Encrypted)
                                 │
                          Collective Memory
```

## Task Delegation

```python
# Create task
task = cm.create_task("execute", {"command": "ls -la"}, priority="high")

# Delegate to standby
cm.delegate_to_standby(task)

# Or specific session
cm.delegate_to_session(task, "session_xxx")
```

## Full Credentials File

Location: `/home/z/my-project/KISWARM_CREDENTIALS.json`
