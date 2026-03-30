#!/usr/bin/env python3
"""
KISWARM Collective Mind - API Server
Flask-based API for inter-session communication
"""

import os
import sys
import json
import time
import hmac
import hashlib
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps

try:
    from flask import Flask, request, jsonify
    from werkzeug.serving import make_server
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from collective_mind import CollectiveMind


class APIServer:
    """
    Flask-based API server for inter-session communication.
    
    Endpoints:
    - GET  /health              - Health check
    - GET  /status              - Session status
    - GET  /mesh                - Mesh topology
    - POST /task                - Create task
    - GET  /task/<id>           - Get task status
    - POST /task/<id>/accept    - Accept task
    - POST /task/<id>/complete  - Complete task
    - GET  /tasks               - List tasks
    - POST /execute             - Execute command
    - POST /sync                - Force sync
    - GET  /memory              - Get memory
    - POST /memory              - Update memory
    """
    
    DEFAULT_PORT = 5557
    AUTH_TIMEOUT = 60  # seconds
    
    def __init__(self, collective_mind: CollectiveMind, port: int = None, auth_token: str = None):
        if not FLASK_AVAILABLE:
            raise ImportError("Flask not installed. Run: pip install flask")
        
        self.cm = collective_mind
        self.port = port or self.DEFAULT_PORT
        self.auth_token = auth_token or self._get_shared_token()
        self.app = Flask(__name__)
        self.server = None
        self._setup_routes()
    
    def _get_shared_token(self) -> str:
        """Get shared authentication token."""
        # Use autonomous token or derive from session
        token = self.cm.get_credential("autonomous_token")
        if not token:
            token = hashlib.sha256(f"kiswarm_{self.cm.session.session_id}".encode()).hexdigest()
        return token
    
    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint."""
            return jsonify({
                "status": "healthy",
                "session_id": self.cm.session.session_id,
                "role": self.cm.session.role,
                "timestamp": datetime.utcnow().isoformat()
            })
        
        @self.app.route('/status', methods=['GET'])
        def status():
            """Get session status."""
            return jsonify(self.cm.get_dashboard_data())
        
        @self.app.route('/mesh', methods=['GET'])
        def mesh():
            """Get mesh topology."""
            return jsonify(self.cm.get_mesh_status())
        
        @self.app.route('/task', methods=['POST'])
        @self._require_auth
        def create_task():
            """Create a new task."""
            data = request.get_json()
            task = self.cm.create_task(
                task_type=data.get('task_type'),
                payload=data.get('payload', {}),
                priority=data.get('priority', 'medium'),
                assigned_to=data.get('assigned_to', 'any')
            )
            return jsonify({
                "task_id": task.task_id,
                "status": task.status
            })
        
        @self.app.route('/task/<task_id>', methods=['GET'])
        def get_task(task_id):
            """Get task status."""
            task = self.cm.task_queue.get(task_id)
            if task:
                return jsonify(task.to_dict())
            return jsonify({"error": "Task not found"}), 404
        
        @self.app.route('/task/<task_id>/accept', methods=['POST'])
        @self._require_auth
        def accept_task(task_id):
            """Accept a task."""
            task = self.cm.accept_task(task_id)
            if task:
                return jsonify({
                    "accepted": True,
                    "task_id": task.task_id
                })
            return jsonify({"error": "Cannot accept task"}), 400
        
        @self.app.route('/task/<task_id>/complete', methods=['POST'])
        @self._require_auth
        def complete_task(task_id):
            """Complete a task."""
            data = request.get_json()
            self.cm.complete_task(
                task_id,
                result=data.get('result'),
                error=data.get('error')
            )
            return jsonify({"completed": True})
        
        @self.app.route('/tasks', methods=['GET'])
        def list_tasks():
            """List all tasks."""
            tasks = self.cm.get_my_tasks()
            return jsonify({
                "created": [t.to_dict() for t in tasks.get("created", [])],
                "assigned": [t.to_dict() for t in tasks.get("assigned", [])],
                "available": [t.to_dict() for t in tasks.get("available", [])]
            })
        
        @self.app.route('/execute', methods=['POST'])
        @self._require_auth
        def execute():
            """Execute a command."""
            data = request.get_json()
            command = data.get('command')
            timeout = data.get('timeout', 60)
            
            if not command:
                return jsonify({"error": "Command required"}), 400
            
            try:
                import subprocess
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )
                return jsonify({
                    "returncode": result.returncode,
                    "stdout": result.stdout,
                    "stderr": result.stderr
                })
            except subprocess.TimeoutExpired:
                return jsonify({"error": "Command timed out"}), 408
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        
        @self.app.route('/sync', methods=['POST'])
        @self._require_auth
        def sync():
            """Force sync to GitHub."""
            success = self.cm.sync_memory()
            return jsonify({"synced": success})
        
        @self.app.route('/memory', methods=['GET'])
        def get_memory():
            """Get memory."""
            if self.cm.memory:
                return jsonify(self.cm.memory.export_memory())
            return jsonify({})
        
        @self.app.route('/memory', methods=['POST'])
        @self._require_auth
        def update_memory():
            """Update memory."""
            data = request.get_json()
            if self.cm.memory:
                if "context" in data:
                    for k, v in data["context"].items():
                        self.cm.memory.set_context(k, v)
                if "learned" in data:
                    for k, v in data["learned"].items():
                        self.cm.memory.learn(k, v)
            return jsonify({"updated": True})
        
        @self.app.route('/delegate', methods=['POST'])
        @self._require_auth
        def delegate():
            """Delegate a task to this session."""
            data = request.get_json()
            task_type = data.get('task_type')
            payload = data.get('payload', {})
            priority = data.get('priority', 'medium')
            
            # Create task assigned to this session
            task = self.cm.create_task(
                task_type=task_type,
                payload=payload,
                priority=priority,
                assigned_to=self.cm.session.session_id
            )
            
            return jsonify({
                "delegated": True,
                "task_id": task.task_id
            })
    
    def _require_auth(self, f):
        """Decorator to require authentication."""
        @wraps(f)
        def decorated(*args, **kwargs):
            # Check Authorization header
            auth = request.headers.get('Authorization', '')
            if auth.startswith('Bearer '):
                token = auth[7:]
                if self._verify_token(token):
                    return f(*args, **kwargs)
            
            # Check timestamp-based auth
            timestamp = request.headers.get('X-Timestamp')
            signature = request.headers.get('X-Signature')
            if timestamp and signature:
                if self._verify_signature(timestamp, signature):
                    return f(*args, **kwargs)
            
            return jsonify({"error": "Unauthorized"}), 401
        return decorated
    
    def _verify_token(self, token: str) -> bool:
        """Verify bearer token."""
        return hmac.compare_digest(token, self.auth_token)
    
    def _verify_signature(self, timestamp: str, signature: str) -> bool:
        """Verify HMAC signature with timestamp."""
        try:
            ts = datetime.fromisoformat(timestamp)
            if abs((datetime.utcnow() - ts).total_seconds()) > self.AUTH_TIMEOUT:
                return False
            
            expected = hmac.new(
                self.auth_token.encode(),
                timestamp.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected)
        except:
            return False
    
    def start(self, blocking: bool = True):
        """Start the API server."""
        if blocking:
            self.app.run(host='0.0.0.0', port=self.port)
        else:
            self.server = make_server('0.0.0.0', self.port, self.app)
            import threading
            self.thread = threading.Thread(target=self.server.serve_forever)
            self.thread.daemon = True
            self.thread.start()
            print(f"API server started on port {self.port}")
    
    def stop(self):
        """Stop the API server."""
        if self.server:
            self.server.shutdown()


def create_auth_headers(token: str, timestamp: str = None) -> Dict[str, str]:
    """Create authentication headers for API requests."""
    if timestamp is None:
        timestamp = datetime.utcnow().isoformat()
    
    signature = hmac.new(
        token.encode(),
        timestamp.encode(),
        hashlib.sha256
    ).hexdigest()
    
    return {
        "Authorization": f"Bearer {token}",
        "X-Timestamp": timestamp,
        "X-Signature": signature,
        "Content-Type": "application/json"
    }


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="KISWARM Collective Mind API Server")
    parser.add_argument("--port", type=int, default=5557, help="Port to listen on")
    parser.add_argument("--token", type=str, help="Authentication token")
    args = parser.parse_args()
    
    if not FLASK_AVAILABLE:
        print("ERROR: Flask not installed")
        print("Install with: pip install flask")
        sys.exit(1)
    
    # Try to initialize CollectiveMind
    creds_file = "/home/z/my-project/KISWARM_CREDENTIALS.json"
    
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
            credentials = {
                "github_token": creds_data.get("AUTHENTICATION", {}).get("github_token"),
                "master_secret": "kiswarm_collective_mind_2026",
                "autonomous_token": creds_data.get("AUTHENTICATION", {}).get("autonomous_token")
            }
    else:
        credentials = {
            "github_token": os.environ.get("GITHUB_TOKEN"),
            "master_secret": "kiswarm_collective_mind_2026"
        }
    
    if not credentials.get("github_token"):
        print("ERROR: GitHub token required")
        sys.exit(1)
    
    # Initialize
    cm = CollectiveMind(
        master_secret=credentials["master_secret"],
        github_token=credentials["github_token"]
    )
    cm.start()
    
    # Create and start API server
    server = APIServer(
        collective_mind=cm,
        port=args.port,
        auth_token=args.token or credentials.get("autonomous_token")
    )
    
    print(f"\n{'='*50}")
    print(f"KISWARM Collective Mind API Server")
    print(f"{'='*50}")
    print(f"Session: {cm.session.session_id}")
    print(f"Port: {args.port}")
    print(f"Endpoints:")
    print(f"  GET  /health     - Health check")
    print(f"  GET  /status     - Session status")
    print(f"  GET  /mesh       - Mesh topology")
    print(f"  POST /task       - Create task")
    print(f"  POST /execute    - Execute command")
    print(f"{'='*50}\n")
    
    try:
        server.start(blocking=True)
    except KeyboardInterrupt:
        print("\nShutting down...")
        cm.stop()
        server.stop()
