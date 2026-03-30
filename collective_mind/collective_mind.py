#!/usr/bin/env python3
"""
KISWARM Collective Mind - Main Orchestrator
Distributed AI consciousness for session continuity and task delegation
"""

import os
import sys
import json
import time
import threading
import signal
from datetime import datetime
from typing import Dict, Any, Optional, List, Callable

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from crypto_manager import CryptoManager, CredentialStore
from session_registry import SessionRegistry, SessionState, SessionInfo
from task_manager import TaskManager, TaskQueue, Task, TaskType, TaskStatus, create_execute_task
from github_sync import GitHubSync, GitHubConfig, MemoryManager


class CollectiveMind:
    """
    Main orchestrator for the KISWARM Collective Mind.
    
    Provides:
    - Session registration and discovery
    - Encrypted memory sync to GitHub
    - Task delegation between sessions
    - Recovery from drift/failure
    """
    
    DEFAULT_STORAGE_DIR = "/home/z/my-project/collective_mind"
    
    def __init__(
        self,
        master_secret: str,
        github_token: str,
        session_role: str = "standby",
        storage_dir: str = None
    ):
        """
        Initialize Collective Mind.
        
        Args:
            master_secret: Secret for encrypting data
            github_token: GitHub personal access token
            session_role: Initial role (active, standby, worker)
            storage_dir: Directory for local storage
        """
        self.storage_dir = storage_dir or self.DEFAULT_STORAGE_DIR
        os.makedirs(self.storage_dir, exist_ok=True)
        
        # Initialize components
        self._init_crypto(master_secret)
        self._init_registry()
        self._init_github(github_token)
        self._init_task_manager()
        self._init_memory()
        
        # Register this session
        self.session = self.registry.register_session(
            role=session_role,
            capabilities=self._get_capabilities()
        )
        
        # Start background services
        self._running = False
        self._threads: List[threading.Thread] = []
        
    def _init_crypto(self, master_secret: str):
        """Initialize crypto manager."""
        # Generate consistent session ID for crypto
        session_id = self._load_or_create_session_id()
        self.crypto = CryptoManager(master_secret, session_id)
        self.credentials = CredentialStore(self.crypto)
    
    def _load_or_create_session_id(self) -> str:
        """Load existing session ID or create new one."""
        session_file = os.path.join(self.storage_dir, "session_id.txt")
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                return f.read().strip()
        
        import uuid
        session_id = f"session_{uuid.uuid4().hex[:12]}"
        with open(session_file, 'w') as f:
            f.write(session_id)
        return session_id
    
    def _init_registry(self):
        """Initialize session registry."""
        self.registry = SessionRegistry(self.storage_dir)
    
    def _init_github(self, token: str):
        """Initialize GitHub sync."""
        config = GitHubConfig(token=token)
        try:
            self.github = GitHubSync(config, self.crypto)
            self.github_available = True
        except Exception as e:
            print(f"Warning: GitHub sync not available: {e}")
            self.github = None
            self.github_available = False
    
    def _init_task_manager(self):
        """Initialize task manager."""
        self.task_queue = TaskQueue(self.storage_dir)
        self.task_manager = TaskManager(self.task_queue, self.session.session_id if hasattr(self, 'session') else "unknown")
        
        # Register default task handlers
        self._register_default_handlers()
    
    def _init_memory(self):
        """Initialize memory manager."""
        if self.github:
            self.memory = MemoryManager(self.github, self.crypto)
        else:
            self.memory = None
    
    def _get_capabilities(self) -> List[str]:
        """Get list of capabilities this session has."""
        return [
            "code", "research", "execute", "analyze",
            "web_search", "file_operations", "git",
            "ssh", "api_calls"
        ]
    
    def _register_default_handlers(self):
        """Register default task handlers."""
        # Execute handler - runs shell commands
        def execute_handler(payload: Dict) -> Dict:
            import subprocess
            command = payload.get("command")
            cwd = payload.get("cwd")
            env = payload.get("env")
            
            result = subprocess.run(
                command,
                shell=True,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            }
        
        self.task_manager.register_handler("execute", execute_handler)
    
    # ==================== CORE OPERATIONS ====================
    
    def start(self):
        """Start all background services."""
        if self._running:
            return
        
        self._running = True
        
        # Heartbeat thread
        self._threads.append(threading.Thread(
            target=self._heartbeat_loop,
            daemon=True
        ))
        
        # Memory sync thread
        if self.github:
            self._threads.append(threading.Thread(
                target=self._memory_sync_loop,
                daemon=True
            ))
        
        # Task check thread
        self._threads.append(threading.Thread(
            target=self._task_check_loop,
            daemon=True
        ))
        
        # Start all threads
        for thread in self._threads:
            thread.start()
        
        print(f"Collective Mind started - Session: {self.session.session_id}")
    
    def stop(self):
        """Stop all background services."""
        self._running = False
        # Set offline status
        if self.session:
            self.registry.update_state("offline")
        print("Collective Mind stopped")
    
    def _heartbeat_loop(self):
        """Send heartbeat every 30 seconds."""
        while self._running:
            try:
                self.registry.heartbeat()
            except Exception as e:
                print(f"Heartbeat error: {e}")
            time.sleep(30)
    
    def _memory_sync_loop(self):
        """Sync memory to GitHub every 5 minutes."""
        while self._running:
            try:
                if self.memory:
                    # Sync registry
                    self.github.upload_encrypted(
                        "registry",
                        {"sessions": {s.session_id: s.to_dict() for s in self.registry.get_all_sessions()}}
                    )
                    # Sync tasks
                    self.github.upload_encrypted(
                        "tasks",
                        {"tasks": [t.to_dict() for t in self.task_queue.tasks.values()]}
                    )
            except Exception as e:
                print(f"Memory sync error: {e}")
            time.sleep(300)  # 5 minutes
    
    def _task_check_loop(self):
        """Check for new tasks every 10 seconds."""
        while self._running:
            try:
                # Check for timed out tasks
                self.task_manager.check_timeouts()
                
                # Get tasks assigned to me
                my_tasks = self.task_manager.get_my_tasks()
                
                # Auto-accept broadcast tasks if standby
                if self.session.role == "standby":
                    for task in my_tasks.get("available", []):
                        if task.priority == "high" or task.priority == "critical":
                            accepted = self.task_manager.accept_task(task.task_id)
                            if accepted:
                                print(f"Auto-accepted high priority task: {task.task_id}")
                
            except Exception as e:
                print(f"Task check error: {e}")
            time.sleep(10)
    
    # ==================== SESSION MANAGEMENT ====================
    
    def set_active(self):
        """Set this session as active (user is interacting)."""
        self.registry.set_active()
        print("Session set to ACTIVE")
    
    def set_standby(self):
        """Set this session as standby (ready but idle)."""
        self.registry.set_standby()
        print("Session set to STANDBY")
    
    def set_worker(self, task_id: str = None):
        """Set this session as worker (executing task)."""
        self.registry.set_worker(task_id)
        print(f"Session set to WORKER (task: {task_id})")
    
    def get_sessions(self) -> List[SessionInfo]:
        """Get all active sessions."""
        return self.registry.get_active_sessions()
    
    def get_mesh_status(self) -> Dict[str, Any]:
        """Get mesh network status."""
        return self.registry.get_mesh_topology()
    
    # ==================== TASK DELEGATION ====================
    
    def create_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: str = "medium",
        assigned_to: str = "any"
    ) -> Task:
        """Create a new task."""
        return self.task_manager.create_task(
            task_type=task_type,
            payload=payload,
            priority=priority,
            assigned_to=assigned_to
        )
    
    def delegate_to_session(self, task: Task, session_id: str) -> bool:
        """Delegate task to specific session."""
        return self.task_manager.delegate_task(task, session_id)
    
    def delegate_to_standby(self, task: Task) -> Optional[str]:
        """Delegate task to an available standby session."""
        worker = self.registry.find_available_worker()
        if worker:
            self.task_manager.delegate_task(task, worker.session_id)
            return worker.session_id
        return None
    
    def accept_task(self, task_id: str) -> Optional[Task]:
        """Accept a task assigned to this session."""
        return self.task_manager.accept_task(task_id)
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None):
        """Mark task as completed."""
        self.task_manager.complete_task(task_id, result, error)
    
    def get_my_tasks(self) -> Dict[str, List[Task]]:
        """Get tasks created by and assigned to this session."""
        return self.task_manager.get_my_tasks()
    
    # ==================== MEMORY OPERATIONS ====================
    
    def sync_memory(self) -> bool:
        """Force immediate memory sync to GitHub."""
        if not self.github:
            return False
        
        try:
            results = self.github.sync_all(
                memory=self.memory.export_memory() if self.memory else {},
                registry={"sessions": {s.session_id: s.to_dict() for s in self.registry.get_all_sessions()}},
                tasks={"tasks": [t.to_dict() for t in self.task_queue.tasks.values()]},
                credentials=self.credentials.get_all()
            )
            return all(results.values())
        except Exception as e:
            print(f"Sync failed: {e}")
            return False
    
    def pull_memory(self) -> bool:
        """Pull latest memory from GitHub."""
        if not self.github:
            return False
        
        try:
            data = self.github.pull_all()
            
            # Import registry
            if data.get("registry"):
                registry_data = data["registry"]
                self.registry.import_from_github(json.dumps(registry_data))
            
            # Import memory
            if data.get("memory") and self.memory:
                self.memory.import_memory(data["memory"])
            
            # Import credentials
            if data.get("credentials"):
                self.credentials.store_all(data["credentials"])
            
            return True
        except Exception as e:
            print(f"Pull failed: {e}")
            return False
    
    def store_credential(self, key: str, value: Any):
        """Store a credential."""
        self.credentials.store(key, value)
    
    def get_credential(self, key: str, default: Any = None) -> Any:
        """Get a credential."""
        return self.credentials.get(key, default)
    
    # ==================== RECOVERY ====================
    
    def recover(self) -> Dict[str, Any]:
        """
        Recover state from GitHub after drift/failure.
        
        Returns recovery status.
        """
        print("Starting recovery from GitHub...")
        
        status = {
            "memory": False,
            "credentials": False,
            "tasks": False,
            "registry": False
        }
        
        if not self.github:
            print("GitHub not available for recovery")
            return status
        
        try:
            # Pull all data
            data = self.github.pull_all()
            
            # Restore memory
            if data.get("memory") and self.memory:
                self.memory.import_memory(data["memory"])
                status["memory"] = True
                print("✓ Memory recovered")
            
            # Restore credentials
            if data.get("credentials"):
                self.credentials.store_all(data["credentials"])
                status["credentials"] = True
                print("✓ Credentials recovered")
            
            # Restore tasks
            if data.get("tasks"):
                for task_data in data["tasks"].get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.task_queue.add(task)
                status["tasks"] = True
                print("✓ Tasks recovered")
            
            # Restore registry (but keep our session)
            if data.get("registry"):
                registry_json = json.dumps(data["registry"])
                self.registry.import_from_github(registry_json)
                status["registry"] = True
                print("✓ Registry recovered")
            
        except Exception as e:
            print(f"Recovery error: {e}")
        
        return status
    
    # ==================== DASHBOARD ====================
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display."""
        sessions = self.get_sessions()
        tasks = self.task_manager.get_status_report()
        
        return {
            "current_session": {
                "id": self.session.session_id,
                "role": self.session.role,
                "started": self.session.started_at
            },
            "mesh": {
                "total": len(sessions),
                "active": len([s for s in sessions if s.role == "active"]),
                "standby": len([s for s in sessions if s.role == "standby"]),
                "worker": len([s for s in sessions if s.role == "worker"]),
                "sessions": [s.to_dict() for s in sessions]
            },
            "tasks": tasks,
            "memory": {
                "events": len(self.memory._memory.get("history", [])) if self.memory else 0,
                "context_keys": list(self.memory._memory.get("context", {}).keys()) if self.memory else [],
                "learned_keys": list(self.memory._memory.get("learned", {}).keys()) if self.memory else []
            },
            "github": {
                "available": self.github_available,
                "last_sync": self.memory._last_sync if self.memory else None
            }
        }
    
    def print_status(self):
        """Print current status to console."""
        data = self.get_dashboard_data()
        
        print("\n" + "="*60)
        print("KISWARM COLLECTIVE MIND - STATUS")
        print("="*60)
        
        print(f"\n📍 Current Session: {data['current_session']['id']}")
        print(f"   Role: {data['current_session']['role'].upper()}")
        print(f"   Started: {data['current_session']['started']}")
        
        print(f"\n🌐 Mesh Network:")
        print(f"   Total Sessions: {data['mesh']['total']}")
        print(f"   Active: {data['mesh']['active']}, Standby: {data['mesh']['standby']}, Worker: {data['mesh']['worker']}")
        
        for session in data['mesh']['sessions']:
            status = "●" if session['is_alive'] else "○"
            print(f"   {status} {session['session_id']}: {session['role']}")
        
        print(f"\n📋 Tasks:")
        print(f"   Pending: {data['tasks']['pending']}, Running: {data['tasks']['running']}")
        print(f"   Completed: {data['tasks']['completed']}, Failed: {data['tasks']['failed']}")
        
        print(f"\n💾 Memory:")
        print(f"   Events: {data['memory']['events']}")
        print(f"   Context: {len(data['memory']['context_keys'])} keys")
        print(f"   Learned: {len(data['memory']['learned_keys'])} items")
        
        print(f"\n☁️ GitHub Sync:")
        print(f"   Available: {'Yes' if data['github']['available'] else 'No'}")
        if data['github']['last_sync']:
            print(f"   Last Sync: {data['github']['last_sync']}")
        
        print("="*60 + "\n")


# ==================== INITIALIZATION HELPER ====================

def initialize_from_credentials(credentials: Dict[str, Any]) -> CollectiveMind:
    """
    Initialize Collective Mind from credentials dict.
    
    Args:
        credentials: Dict containing:
            - master_secret: Secret for encryption
            - github_token: GitHub PAT
            
    Returns:
        Initialized CollectiveMind instance
    """
    master_secret = credentials.get("master_secret", "kiswarm_default_secret_2026")
    github_token = credentials.get("github_token") or credentials.get("GITHUB_TOKEN")
    
    if not github_token:
        raise ValueError("GitHub token required for Collective Mind")
    
    cm = CollectiveMind(
        master_secret=master_secret,
        github_token=github_token,
        session_role="active"
    )
    
    # Store all provided credentials
    for key, value in credentials.items():
        if key not in ("master_secret", "github_token"):
            cm.store_credential(key, value)
    
    return cm


# ==================== MAIN ====================

if __name__ == "__main__":
    print("="*60)
    print("KISWARM COLLECTIVE MIND")
    print("="*60)
    
    # Try to load credentials
    creds_file = "/home/z/my-project/KISWARM_CREDENTIALS.json"
    credentials = {}
    
    if os.path.exists(creds_file):
        with open(creds_file, 'r') as f:
            creds_data = json.load(f)
            # Flatten credentials
            auth = creds_data.get("AUTHENTICATION", {})
            credentials["github_token"] = auth.get("github_token")
            credentials["master_secret"] = "kiswarm_collective_mind_2026"
    
    if not credentials.get("github_token"):
        print("ERROR: GitHub token required")
        print("Set GITHUB_TOKEN environment variable or create credentials file")
        sys.exit(1)
    
    # Initialize
    cm = initialize_from_credentials(credentials)
    
    # Start services
    cm.start()
    
    # Print status
    cm.print_status()
    
    # Try recovery
    print("Attempting recovery from GitHub...")
    recovery = cm.recover()
    print(f"Recovery status: {recovery}")
    
    # Keep running
    print("\nCollective Mind is running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(60)
            cm.registry.heartbeat()
    except KeyboardInterrupt:
        cm.stop()
        print("\nGoodbye!")
