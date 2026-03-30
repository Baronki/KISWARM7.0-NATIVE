#!/usr/bin/env python3
"""
KISWARM Session Hub - Central coordination server
Runs on UpCloud at port 5558

Provides:
- Session registration and discovery
- Heartbeat tracking
- Bidirectional messaging
- Shared memory
"""

from flask import Flask, request, jsonify
import redis
import json
import time
import os
from datetime import datetime, timedelta
from functools import wraps

app = Flask(__name__)

# Configuration
AUTONOMOUS_TOKEN = os.environ.get('AUTONOMOUS_TOKEN', 'ada6952188dce59c207b9a61183e8004')
HEARTBEAT_TIMEOUT = int(os.environ.get('HEARTBEAT_TIMEOUT', 120))
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))

# Redis connection
try:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    r.ping()
    REDIS_AVAILABLE = True
except:
    REDIS_AVAILABLE = False
    print("Warning: Redis not available, using in-memory storage")
    _memory_store = {}
    _session_store = {}
    _message_store = {}

# Auth decorator
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        token = auth.replace('Bearer ', '') if auth.startswith('Bearer ') else auth
        
        if token != AUTONOMOUS_TOKEN:
            return jsonify({"error": "unauthorized", "message": "Invalid token"}), 401
        return f(*args, **kwargs)
    return decorated

# Storage abstraction
def store_hset(name, key, value):
    if REDIS_AVAILABLE:
        r.hset(name, key, json.dumps(value) if isinstance(value, (dict, list)) else value)
    else:
        if name not in _memory_store:
            _memory_store[name] = {}
        _memory_store[name][key] = value

def store_hget(name, key):
    if REDIS_AVAILABLE:
        val = r.hget(name, key)
        if val:
            try:
                return json.loads(val)
            except:
                return val
        return None
    else:
        return _memory_store.get(name, {}).get(key)

def store_hgetall(name):
    if REDIS_AVAILABLE:
        return {k: json.loads(v) if v.startswith('{') or v.startswith('[') else v 
                for k, v in r.hgetall(name).items()}
    else:
        return _memory_store.get(name, {})

def store_hvals(name):
    if REDIS_AVAILABLE:
        return [json.loads(v) if v.startswith('{') or v.startswith('[') else v 
                for v in r.hvals(name)]
    else:
        return list(_memory_store.get(name, {}).values())

def store_hlen(name):
    if REDIS_AVAILABLE:
        return r.hlen(name)
    else:
        return len(_memory_store.get(name, {}))

def store_rpush(name, value):
    if REDIS_AVAILABLE:
        r.rpush(name, json.dumps(value))
    else:
        if name not in _message_store:
            _message_store[name] = []
        _message_store[name].append(value)

def store_lpop(name):
    if REDIS_AVAILABLE:
        val = r.lpop(name)
        if val:
            try:
                return json.loads(val)
            except:
                return val
        return None
    else:
        if name in _message_store and _message_store[name]:
            return _message_store[name].pop(0)
        return None

def store_llen(name):
    if REDIS_AVAILABLE:
        return r.llen(name)
    else:
        return len(_message_store.get(name, []))

# API Routes

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "healthy",
        "redis": "connected" if REDIS_AVAILABLE else "in-memory",
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/session/register', methods=['POST'])
@auth_required
def register_session():
    """Register a new session."""
    data = request.json
    
    if not data or 'session_id' not in data:
        return jsonify({"error": "missing session_id"}), 400
    
    session_id = data['session_id']
    now = datetime.utcnow().isoformat()
    
    session_data = {
        'session_id': session_id,
        'role': data.get('role', 'standby'),
        'capabilities': data.get('capabilities', []),
        'started_at': data.get('started_at', now),
        'last_seen': now,
        'status': 'active',
        'metadata': data.get('metadata', {})
    }
    
    store_hset('sessions', session_id, session_data)
    
    # Get existing sessions (excluding self)
    existing = [s for s in store_hvals('sessions') 
                if isinstance(s, dict) and s.get('session_id') != session_id]
    
    return jsonify({
        'status': 'registered',
        'session_id': session_id,
        'hub_time': now,
        'existing_sessions': existing
    })

@app.route('/session/heartbeat', methods=['POST'])
@auth_required
def heartbeat():
    """Update session heartbeat."""
    data = request.json
    
    if not data or 'session_id' not in data:
        return jsonify({"error": "missing session_id"}), 400
    
    session_id = data['session_id']
    
    # Get existing session
    session = store_hget('sessions', session_id)
    if session:
        session['last_seen'] = datetime.utcnow().isoformat()
        session['status'] = data.get('status', 'active')
        if 'current_task' in data:
            session['current_task'] = data['current_task']
        store_hset('sessions', session_id, session)
    
    # Count messages waiting
    msg_count = store_llen(f'messages:{session_id}')
    
    return jsonify({
        'status': 'acknowledged',
        'active_sessions': store_hlen('sessions'),
        'messages_waiting': msg_count,
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/session/discover', methods=['GET'])
@auth_required
def discover():
    """Discover all active sessions."""
    sessions = []
    now = datetime.utcnow()
    
    for session in store_hvals('sessions'):
        if not isinstance(session, dict):
            continue
            
        last_seen_str = session.get('last_seen', '2000-01-01T00:00:00')
        try:
            last_seen = datetime.fromisoformat(last_seen_str)
            if (now - last_seen).total_seconds() > HEARTBEAT_TIMEOUT:
                session['status'] = 'stale'
            else:
                session['status'] = 'healthy'
        except:
            session['status'] = 'unknown'
        
        sessions.append(session)
    
    return jsonify({
        'sessions': sessions,
        'total': len(sessions),
        'healthy': len([s for s in sessions if s.get('status') == 'healthy']),
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/session/status/<session_id>', methods=['GET'])
@auth_required
def session_status(session_id):
    """Get status of a specific session."""
    session = store_hget('sessions', session_id)
    if not session:
        return jsonify({"error": "session not found"}), 404
    
    return jsonify(session)

@app.route('/message/send', methods=['POST'])
@auth_required
def send_message():
    """Send a message to another session."""
    data = request.json
    
    if not data or 'to' not in data:
        return jsonify({"error": "missing 'to' field"}), 400
    
    message_id = f"msg_{int(time.time()*1000)}_{os.urandom(4).hex()}"
    
    message = {
        'message_id': message_id,
        'from': data.get('from', 'unknown'),
        'to': data['to'],
        'type': data.get('type', 'generic'),
        'priority': data.get('priority', 'normal'),
        'payload': data.get('payload', {}),
        'requires_ack': data.get('requires_ack', False),
        'timestamp': datetime.utcnow().isoformat()
    }
    
    store_rpush(f'messages:{data["to"]}', message)
    
    return jsonify({
        'status': 'queued',
        'message_id': message_id,
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/message/receive', methods=['GET'])
@auth_required
def receive_messages():
    """Receive pending messages for a session."""
    session_id = request.args.get('session_id')
    
    if not session_id:
        return jsonify({"error": "missing session_id"}), 400
    
    messages = []
    
    # Get all pending messages
    while True:
        msg = store_lpop(f'messages:{session_id}')
        if not msg:
            break
        messages.append(msg)
    
    return jsonify({
        'messages': messages,
        'count': len(messages),
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/message/ack', methods=['POST'])
@auth_required
def ack_message():
    """Acknowledge a message."""
    data = request.json
    
    # Store acknowledgment
    ack_key = f"ack:{data.get('message_id')}"
    store_hset('acks', ack_key, {
        'message_id': data.get('message_id'),
        'session_id': data.get('session_id'),
        'status': data.get('status', 'acknowledged'),
        'response': data.get('response', {}),
        'timestamp': datetime.utcnow().isoformat()
    })
    
    return jsonify({'status': 'acknowledged'})

@app.route('/memory/write', methods=['POST'])
@auth_required
def write_memory():
    """Write to shared memory."""
    data = request.json
    
    if not data or 'key' not in data:
        return jsonify({"error": "missing key"}), 400
    
    key = data['key']
    value = data.get('value')
    
    # Handle merge
    if data.get('merge'):
        existing = store_hget('memory', key)
        if existing and isinstance(existing, dict) and isinstance(value, dict):
            existing.update(value)
            value = existing
    
    store_hset('memory', key, value)
    store_hset('memory_meta', key, {
        'last_written': datetime.utcnow().isoformat(),
        'written_by': data.get('session_id', 'unknown')
    })
    
    return jsonify({
        'status': 'written',
        'key': key,
        'hub_time': datetime.utcnow().isoformat()
    })

@app.route('/memory/read', methods=['GET'])
@auth_required
def read_memory():
    """Read from shared memory."""
    key = request.args.get('key')
    
    if not key:
        return jsonify({"error": "missing key"}), 400
    
    value = store_hget('memory', key)
    meta = store_hget('memory_meta', key)
    
    return jsonify({
        'key': key,
        'value': value,
        'meta': meta
    })

@app.route('/memory/list', methods=['GET'])
@auth_required
def list_memory():
    """List all memory keys."""
    pattern = request.args.get('pattern', '*')
    
    all_keys = list(store_hgetall('memory').keys())
    
    if pattern == '*':
        keys = all_keys
    else:
        import fnmatch
        keys = [k for k in all_keys if fnmatch.fnmatch(k, pattern)]
    
    return jsonify({
        'keys': keys,
        'count': len(keys)
    })

@app.route('/sync', methods=['POST'])
@auth_required
def sync():
    """Full sync with hub."""
    data = request.json
    session_id = data.get('session_id', 'unknown')
    direction = data.get('direction', 'both')
    
    result = {
        'status': 'synced',
        'sync_time': datetime.utcnow().isoformat()
    }
    
    # Store local state from session
    if direction in ('both', 'upload') and 'local_state' in data:
        local_state = data['local_state']
        
        # Store memory
        for key, value in local_state.get('memory', {}).items():
            store_hset('memory', f'session:{session_id}:{key}', value)
        
        # Store tasks
        for task in local_state.get('tasks', []):
            if isinstance(task, dict) and 'task_id' in task:
                store_hset('tasks', task['task_id'], task)
    
    # Return remote state
    if direction in ('both', 'download'):
        result['remote_state'] = {
            'memory': store_hgetall('memory'),
            'sessions': store_hvals('sessions'),
            'tasks': store_hvals('tasks')
        }
    
    return result

@app.route('/task/create', methods=['POST'])
@auth_required
def create_task():
    """Create a task that can be picked up by any session."""
    data = request.json
    
    import uuid
    task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    task = {
        'task_id': task_id,
        'type': data.get('type', 'generic'),
        'priority': data.get('priority', 'normal'),
        'created_by': data.get('created_by', 'unknown'),
        'assigned_to': data.get('assigned_to', 'any'),
        'status': 'pending',
        'payload': data.get('payload', {}),
        'created_at': datetime.utcnow().isoformat()
    }
    
    store_hset('tasks', task_id, task)
    
    # Notify sessions if broadcast
    if task['assigned_to'] == 'any':
        for session in store_hvals('sessions'):
            if isinstance(session, dict) and session.get('session_id'):
                store_rpush(f'messages:{session["session_id"]}', {
                    'message_id': f'notify_{task_id}',
                    'type': 'new_task',
                    'task_id': task_id,
                    'priority': task['priority'],
                    'timestamp': datetime.utcnow().isoformat()
                })
    
    return jsonify({
        'status': 'created',
        'task_id': task_id
    })

@app.route('/task/<task_id>', methods=['GET'])
@auth_required
def get_task(task_id):
    """Get task status."""
    task = store_hget('tasks', task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    return jsonify(task)

@app.route('/task/<task_id>/accept', methods=['POST'])
@auth_required
def accept_task(task_id):
    """Accept a task."""
    session_id = request.json.get('session_id')
    
    task = store_hget('tasks', task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    
    if task.get('status') != 'pending':
        return jsonify({"error": "task not available"}), 400
    
    task['status'] = 'running'
    task['assigned_to'] = session_id
    task['started_at'] = datetime.utcnow().isoformat()
    
    store_hset('tasks', task_id, task)
    
    return jsonify({
        'status': 'accepted',
        'task': task
    })

@app.route('/task/<task_id>/complete', methods=['POST'])
@auth_required
def complete_task(task_id):
    """Complete a task."""
    data = request.json
    
    task = store_hget('tasks', task_id)
    if not task:
        return jsonify({"error": "task not found"}), 404
    
    task['status'] = 'completed' if not data.get('error') else 'failed'
    task['completed_at'] = datetime.utcnow().isoformat()
    task['result'] = data.get('result')
    if data.get('error'):
        task['error'] = data.get('error')
    
    store_hset('tasks', task_id, task)
    
    return jsonify({
        'status': task['status'],
        'task': task
    })


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='KISWARM Session Hub')
    parser.add_argument('--port', type=int, default=5558, help='Port to listen on')
    parser.add_argument('--token', type=str, help='Authentication token')
    parser.add_argument('--redis-host', type=str, help='Redis host')
    args = parser.parse_args()
    
    if args.token:
        AUTONOMOUS_TOKEN = args.token
    if args.redis_host:
        REDIS_HOST = args.redis_host
    
    print(f"Starting KISWARM Session Hub on port {args.port}")
    print(f"Redis: {REDIS_HOST}:{REDIS_PORT}")
    print(f"Auth token configured: {'Yes' if AUTONOMOUS_TOKEN else 'No'}")
    
    app.run(host='0.0.0.0', port=args.port, threaded=True)
