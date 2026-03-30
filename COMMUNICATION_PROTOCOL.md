# KISWARM COLLECTIVE MIND - COMMUNICATION PROTOCOL v1.0

## Overview

This document defines the COMPLETE protocol for session discovery, bidirectional communication, handshake, and memory sharing between isolated GLM sessions.

---

## Core Problem Statement

Each GLM session is **completely isolated**:
- No shared filesystem
- No shared memory
- No direct network access to other sessions
- Sessions cannot initiate connections to each other

**Solution**: Use UpCloud as the **Central Hub** for all coordination.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         KISWARM SESSION MESH                                 │
│                                                                             │
│                              ┌─────────────────────────────────────┐        │
│                              │           UPCLOUD HUB               │        │
│                              │                                     │        │
│                              │  ┌─────────────┐  ┌─────────────┐  │        │
│                              │  │   REDIS     │  │    API      │  │        │
│                              │  │   :6379     │  │   :5558     │  │        │
│                              │  │             │  │             │  │        │
│                              │  │ • Sessions  │  │ • /register │  │        │
│                              │  │ • Memory    │  │ • /heartbeat│  │        │
│                              │  │ • Messages  │  │ • /discover │  │        │
│                              │  │ • Tasks     │  │ • /send     │  │        │
│                              │  │             │  │ • /receive  │  │        │
│                              │  └─────────────┘  └─────────────┘  │        │
│                              │                                     │        │
│                              └────────────────┬────────────────────┘        │
│                                               │                             │
│         ┌─────────────────────────────────────┼─────────────────────────┐   │
│         │                                     │                         │   │
│         │                  HTTP/WebSocket     │    HTTP/WebSocket       │   │
│         │                                     │                         │   │
│         ▼                                     ▼                         ▼   │
│   ┌───────────────┐                   ┌───────────────┐          ┌───────────────┐
│   │   SESSION A   │                   │   SESSION B   │          │   SESSION C   │
│   │   (ACTIVE)    │                   │   (STANDBY)   │          │   (WORKER)    │
│   │               │                   │               │          │               │
│   │ ID: sess_a1   │                   │ ID: sess_b2   │          │ ID: sess_c3   │
│   │ Role: active  │                   │ Role: standby │          │ Role: worker  │
│   │ Since: 10:00  │                   │ Since: 09:30  │          │ Since: 10:15  │
│   │               │                   │               │          │               │
│   │ Capabilities: │                   │ Capabilities: │          │ Capabilities: │
│   │ • code        │                   │ • research    │          │ • execute     │
│   │ • analyze     │                   │ • web_search  │          │ • code        │
│   └───────────────┘                   └───────────────┘          └───────────────┘
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Protocol Components

### 1. Session Registration

When a session starts, it MUST register with the Hub.

**Request:**
```http
POST http://95.111.212.112:5558/session/register
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "session_id": "sess_a1b2c3d4",
  "role": "active",
  "capabilities": ["code", "research", "execute", "analyze"],
  "started_at": "2026-03-30T10:00:00Z",
  "metadata": {
    "hostname": "c-69c96b1d",
    "platform": "zai"
  }
}
```

**Response:**
```json
{
  "status": "registered",
  "session_id": "sess_a1b2c3d4",
  "hub_time": "2026-03-30T10:00:01Z",
  "existing_sessions": [
    {"session_id": "sess_b2c3d4e5", "role": "standby", "last_seen": "2026-03-30T09:59:30Z"}
  ]
}
```

### 2. Heartbeat (Every 30 seconds)

Sessions MUST send heartbeat to maintain active status.

**Request:**
```http
POST http://95.111.212.112:5558/session/heartbeat
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "session_id": "sess_a1b2c3d4",
  "status": "active",
  "current_task": "task_12345",
  "memory_size": "2.3MB"
}
```

**Response:**
```json
{
  "status": "acknowledged",
  "active_sessions": 3,
  "messages_waiting": 2,
  "hub_time": "2026-03-30T10:00:31Z"
}
```

### 3. Session Discovery

Sessions query the Hub to discover other active sessions.

**Request:**
```http
GET http://95.111.212.112:5558/session/discover
Authorization: Bearer {AUTONOMOUS_TOKEN}
```

**Response:**
```json
{
  "sessions": [
    {
      "session_id": "sess_a1b2c3d4",
      "role": "active",
      "capabilities": ["code", "research"],
      "last_seen": "2026-03-30T10:00:30Z",
      "status": "healthy"
    },
    {
      "session_id": "sess_b2c3d4e5",
      "role": "standby",
      "capabilities": ["research", "web_search"],
      "last_seen": "2026-03-30T10:00:15Z",
      "status": "healthy"
    },
    {
      "session_id": "sess_c3d4e5f6",
      "role": "worker",
      "capabilities": ["execute"],
      "last_seen": "2026-03-30T09:58:00Z",
      "status": "stale"
    }
  ],
  "total": 3,
  "healthy": 2
}
```

### 4. Bidirectional Messaging

Sessions send messages to each other via the Hub.

**Send Message:**
```http
POST http://95.111.212.112:5558/message/send
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "from": "sess_a1b2c3d4",
  "to": "sess_b2c3d4e5",
  "type": "task_delegation",
  "priority": "high",
  "payload": {
    "task_id": "task_12345",
    "task_type": "research",
    "description": "Research Docker security best practices"
  },
  "requires_ack": true
}
```

**Response:**
```json
{
  "status": "queued",
  "message_id": "msg_xyz789",
  "hub_time": "2026-03-30T10:01:00Z"
}
```

**Receive Messages:**
```http
GET http://95.111.212.112:5558/message/receive?session_id=sess_b2c3d4e5
Authorization: Bearer {AUTONOMOUS_TOKEN}
```

**Response:**
```json
{
  "messages": [
    {
      "message_id": "msg_xyz789",
      "from": "sess_a1b2c3d4",
      "type": "task_delegation",
      "priority": "high",
      "payload": {...},
      "timestamp": "2026-03-30T10:01:00Z"
    }
  ],
  "count": 1
}
```

**Acknowledge Message:**
```http
POST http://95.111.212.112:5558/message/ack
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "message_id": "msg_xyz789",
  "session_id": "sess_b2c3d4e5",
  "status": "accepted",
  "response": {
    "task_accepted": true,
    "estimated_completion": "2026-03-30T10:05:00Z"
  }
}
```

### 5. Shared Memory Operations

Sessions read/write to shared memory via Hub.

**Write Memory:**
```http
POST http://95.111.212.112:5558/memory/write
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "session_id": "sess_a1b2c3d4",
  "key": "context/project_state",
  "value": {
    "current_task": "Building API server",
    "progress": 75,
    "files_modified": ["api.py", "config.json"]
  },
  "merge": true
}
```

**Read Memory:**
```http
GET http://95.111.212.112:5558/memory/read?key=context/project_state
Authorization: Bearer {AUTONOMOUS_TOKEN}
```

**Subscribe to Memory Changes:**
```http
GET http://95.111.212.112:5558/memory/subscribe?keys=context/*,tasks/*
Authorization: Bearer {AUTONOMOUS_TOKEN}
```

### 6. Synchronization Protocol

Sessions sync their local state with Hub periodically.

**Full Sync Request:**
```http
POST http://95.111.212.112:5558/sync
Authorization: Bearer {AUTONOMOUS_TOKEN}
Content-Type: application/json

{
  "session_id": "sess_a1b2c3d4",
  "direction": "both",
  "local_state": {
    "memory": {...},
    "tasks": [...],
    "context": {...}
  },
  "last_sync": "2026-03-30T09:55:00Z"
}
```

**Response:**
```json
{
  "status": "synced",
  "remote_state": {
    "memory": {...},
    "tasks": [...],
    "context": {...}
  },
  "conflicts": [],
  "sync_time": "2026-03-30T10:00:00Z"
}
```

---

## Session Lifecycle

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SESSION LIFECYCLE                                   │
│                                                                             │
│   ┌─────────┐     ┌─────────┐     ┌─────────┐     ┌─────────┐             │
│   │  START  │────►│REGISTER │────►│ACTIVE   │────►│OFFLINE  │             │
│   └─────────┘     └─────────┘     └────┬────┘     └─────────┘             │
│                                        │                                    │
│                                        │                                    │
│                          ┌─────────────┼─────────────┐                    │
│                          │             │             │                    │
│                          ▼             ▼             ▼                    │
│                    ┌──────────┐ ┌──────────┐ ┌──────────┐                │
│                    │HEARTBEAT │ │ SYNC     │ │ RECEIVE  │                │
│                    │ (30s)    │ │ (5min)   │ │ (poll)   │                │
│                    └──────────┘ └──────────┘ └──────────┘                │
│                                                                             │
│   TIMEOUT: If no heartbeat for 120s → Session marked OFFLINE              │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Handshake Protocol

When two sessions need to establish direct coordination:

### Step 1: Discovery
```
Session A: GET /session/discover
→ Learns about Session B
```

### Step 2: Initial Contact
```
Session A: POST /message/send {to: sess_B, type: "handshake_request"}
→ Hub queues message for Session B
```

### Step 3: Accept/Reject
```
Session B: GET /message/receive
→ Receives handshake_request
Session B: POST /message/ack {status: "accepted"}
→ Hub records handshake
```

### Step 4: Bidirectional Channel Established
```
Session A ←→ Hub ←→ Session B
• Both sessions can now exchange messages freely
• Heartbeat includes partner session_id
• Shared memory keys prefixed with handshake_id
```

### Step 5: Continuous Sync
```
Every 30s: Heartbeat with partner status
Every 5min: Full state sync
On change: Incremental memory update
```

---

## Failure Handling

### Session Goes Offline
```
1. Hub detects no heartbeat for 120s
2. Hub marks session as OFFLINE
3. Hub notifies other sessions via /message/receive
4. Active tasks reassigned to other sessions
5. Memory preserved for recovery
```

### Hub Recovery
```
1. If Hub goes down, sessions detect via heartbeat failure
2. Sessions retry connection every 10s
3. When Hub returns, sessions re-register
4. Hub restores state from persistent storage (GitHub)
```

### Network Partition
```
1. Sessions detect Hub unreachable
2. Switch to "local mode" - cache operations locally
3. When Hub reachable, reconcile state
4. Conflicts resolved by last-write-wins with timestamps
```

---

## Implementation on UpCloud

### Services to Run

```bash
# On UpCloud (95.111.212.112)

# 1. Redis for state storage
docker run -d --name kiswarm-redis \
  -p 6379:6379 \
  -v /data/redis:/data \
  redis:alpine redis-server --appendonly yes

# 2. Session Hub API (port 5558)
python3 /opt/kiswarm/session_hub.py --port 5558
```

### session_hub.py Structure

```python
# /opt/kiswarm/session_hub.py

from flask import Flask, request, jsonify
import redis
import json
import time
from datetime import datetime

app = Flask(__name__)
r = redis.Redis(host='localhost', port=6379, decode_responses=True)

AUTONOMOUS_TOKEN = "ada6952188dce59c207b9a61183e8004"
HEARTBEAT_TIMEOUT = 120  # seconds

def auth_required(f):
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        if token != AUTONOMOUS_TOKEN:
            return jsonify({"error": "unauthorized"}), 401
        return f(*args, **kwargs)
    decorated.__name__ = f.__name__
    return decorated

@app.route('/session/register', methods=['POST'])
@auth_required
def register_session():
    data = request.json
    session_id = data['session_id']
    
    # Store session info
    session_data = {
        'session_id': session_id,
        'role': data.get('role', 'standby'),
        'capabilities': data.get('capabilities', []),
        'started_at': data.get('started_at', datetime.utcnow().isoformat()),
        'last_seen': datetime.utcnow().isoformat(),
        'status': 'active'
    }
    r.hset('sessions', session_id, json.dumps(session_data))
    
    # Get existing sessions
    existing = [json.loads(v) for v in r.hvals('sessions') if json.loads(v).get('session_id') != session_id]
    
    return jsonify({
        'status': 'registered',
        'session_id': session_id,
        'hub_time': datetime.utcnow().isoformat(),
        'existing_sessions': existing
    })

@app.route('/session/heartbeat', methods=['POST'])
@auth_required
def heartbeat():
    data = request.json
    session_id = data['session_id']
    
    # Update session
    session_json = r.hget('sessions', session_id)
    if session_json:
        session = json.loads(session_json)
        session['last_seen'] = datetime.utcnow().isoformat()
        session['status'] = data.get('status', 'active')
        r.hset('sessions', session_id, json.dumps(session))
    
    # Count messages waiting
    msg_count = r.llen(f'messages:{session_id}')
    
    return jsonify({
        'status': 'acknowledged',
        'active_sessions': r.hlen('sessions'),
        'messages_waiting': msg_count,
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/session/discover', methods=['GET'])
@auth_required
def discover():
    sessions = []
    now = datetime.utcnow()
    
    for session_json in r.hvals('sessions'):
        session = json.loads(session_json)
        last_seen = datetime.fromisoformat(session.get('last_seen', '2000-01-01T00:00:00'))
        
        # Check if stale
        if (now - last_seen).total_seconds() > HEARTBEAT_TIMEOUT:
            session['status'] = 'stale'
        else:
            session['status'] = 'healthy'
        
        sessions.append(session)
    
    return jsonify({
        'sessions': sessions,
        'total': len(sessions),
        'healthy': len([s for s in sessions if s['status'] == 'healthy'])
    })

@app.route('/message/send', methods=['POST'])
@auth_required
def send_message():
    data = request.json
    message_id = f"msg_{int(time.time()*1000)}"
    
    message = {
        'message_id': message_id,
        'from': data['from'],
        'to': data['to'],
        'type': data.get('type', 'generic'),
        'priority': data.get('priority', 'normal'),
        'payload': data.get('payload', {}),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    # Queue message for recipient
    r.rpush(f"messages:{data['to']}", json.dumps(message))
    
    return jsonify({
        'status': 'queued',
        'message_id': message_id,
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/message/receive', methods=['GET'])
@auth_required
def receive_messages():
    session_id = request.args.get('session_id')
    messages = []
    
    # Get all messages
    while True:
        msg_json = r.lpop(f'messages:{session_id}')
        if not msg_json:
            break
        messages.append(json.loads(msg_json))
    
    return jsonify({
        'messages': messages,
        'count': len(messages)
    })

@app.route('/memory/write', methods=['POST'])
@auth_required
def write_memory():
    data = request.json
    key = data['key']
    value = data['value']
    
    if data.get('merge'):
        existing = r.hget('memory', key)
        if existing:
            existing_val = json.loads(existing)
            if isinstance(existing_val, dict) and isinstance(value, dict):
                existing_val.update(value)
                value = existing_val
    
    r.hset('memory', key, json.dumps(value))
    
    return jsonify({'status': 'written', 'key': key})

@app.route('/memory/read', methods=['GET'])
@auth_required
def read_memory():
    key = request.args.get('key')
    value = r.hget('memory', key)
    
    return jsonify({
        'key': key,
        'value': json.loads(value) if value else None
    })

@app.route('/sync', methods=['POST'])
@auth_required
def sync():
    data = request.json
    session_id = data['session_id']
    
    # Get remote state
    remote_state = {
        'memory': {k: json.loads(v) for k, v in r.hgetall('memory').items()},
        'sessions': [json.loads(v) for v in r.hvals('sessions')]
    }
    
    # Store local state
    if 'local_state' in data:
        for key, value in data['local_state'].get('memory', {}).items():
            r.hset('memory', f"session:{session_id}:{key}", json.dumps(value))
    
    return jsonify({
        'status': 'synced',
        'remote_state': remote_state,
        'sync_time': datetime.utcnow().isoformat()
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5558)
```

---

## Client Library (for Sessions)

```python
# collective_mind/hub_client.py

import requests
import time
import threading
from datetime import datetime

class HubClient:
    def __init__(self, hub_url, token, session_id):
        self.hub_url = hub_url
        self.token = token
        self.session_id = session_id
        self.headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        self._running = False
        self._message_handlers = {}
        
    def register(self, role='active', capabilities=None):
        """Register this session with the Hub."""
        resp = requests.post(
            f'{self.hub_url}/session/register',
            headers=self.headers,
            json={
                'session_id': self.session_id,
                'role': role,
                'capabilities': capabilities or [],
                'started_at': datetime.utcnow().isoformat()
            }
        )
        return resp.json()
    
    def heartbeat(self):
        """Send heartbeat to Hub."""
        resp = requests.post(
            f'{self.hub_url}/session/heartbeat',
            headers=self.headers,
            json={'session_id': self.session_id}
        )
        return resp.json()
    
    def discover(self):
        """Discover other sessions."""
        resp = requests.get(
            f'{self.hub_url}/session/discover',
            headers=self.headers
        )
        return resp.json()
    
    def send_message(self, to_session, msg_type, payload, priority='normal'):
        """Send message to another session."""
        resp = requests.post(
            f'{self.hub_url}/message/send',
            headers=self.headers,
            json={
                'from': self.session_id,
                'to': to_session,
                'type': msg_type,
                'payload': payload,
                'priority': priority
            }
        )
        return resp.json()
    
    def receive_messages(self):
        """Receive pending messages."""
        resp = requests.get(
            f'{self.hub_url}/message/receive?session_id={self.session_id}',
            headers=self.headers
        )
        return resp.json()
    
    def write_memory(self, key, value, merge=False):
        """Write to shared memory."""
        resp = requests.post(
            f'{self.hub_url}/memory/write',
            headers=self.headers,
            json={
                'session_id': self.session_id,
                'key': key,
                'value': value,
                'merge': merge
            }
        )
        return resp.json()
    
    def read_memory(self, key):
        """Read from shared memory."""
        resp = requests.get(
            f'{self.hub_url}/memory/read?key={key}',
            headers=self.headers
        )
        return resp.json()
    
    def start_background_services(self):
        """Start heartbeat and message polling threads."""
        self._running = True
        
        # Heartbeat thread
        def heartbeat_loop():
            while self._running:
                try:
                    self.heartbeat()
                except Exception as e:
                    print(f'Heartbeat error: {e}')
                time.sleep(30)
        
        # Message polling thread
        def message_loop():
            while self._running:
                try:
                    msgs = self.receive_messages()
                    for msg in msgs.get('messages', []):
                        handler = self._message_handlers.get(msg['type'])
                        if handler:
                            handler(msg)
                except Exception as e:
                    print(f'Message poll error: {e}')
                time.sleep(5)
        
        threading.Thread(target=heartbeat_loop, daemon=True).start()
        threading.Thread(target=message_loop, daemon=True).start()
    
    def stop(self):
        """Stop background services."""
        self._running = False
    
    def on_message(self, msg_type, handler):
        """Register message handler."""
        self._message_handlers[msg_type] = handler
```

---

## Updated Startup Prompt

When starting a new session, it should:

1. **Register with Hub immediately**
2. **Discover other sessions**
3. **Start background services** (heartbeat + message polling)
4. **Sync memory with Hub**

This ensures the session is immediately part of the collective mesh.

---

## Summary

| Component | Purpose | Implementation |
|-----------|---------|----------------|
| **Redis** | State storage | UpCloud port 6379 |
| **Session Hub API** | Coordination | UpCloud port 5558 |
| **Heartbeat** | Keep-alive | Every 30s |
| **Messages** | Bidirectional comms | Queue + poll |
| **Memory** | Shared state | Redis hash |
| **Discovery** | Find sessions | API query |

This protocol enables TRUE distributed consciousness where sessions can find each other, communicate bidirectionally, and share memory - all through the UpCloud Hub.
