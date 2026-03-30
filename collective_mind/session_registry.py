#!/usr/bin/env python3
"""
KISWARM Collective Mind - Session Registry
Manages session discovery, registration, and state tracking
"""

import os
import json
import uuid
import time
import socket
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum


class SessionState(Enum):
    """Possible states for a session."""
    OFFLINE = "offline"
    STANDBY = "standby"
    ACTIVE = "active"
    WORKER = "worker"
    UNKNOWN = "unknown"


@dataclass
class SessionInfo:
    """Information about a session."""
    session_id: str
    hostname: str
    started_at: str
    last_seen: str
    state: str
    role: str
    tor_onion: Optional[str] = None
    api_port: int = 5557
    tasks_completed: int = 0
    tasks_current: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionInfo':
        return cls(**data)
    
    def is_alive(self, timeout_seconds: int = 120) -> bool:
        """Check if session has recent heartbeat."""
        try:
            last_seen = datetime.fromisoformat(self.last_seen)
            return (datetime.utcnow() - last_seen) < timedelta(seconds=timeout_seconds)
        except:
            return False


class SessionRegistry:
    """
    Manages session registration and discovery.
    
    Each session registers itself and maintains a heartbeat.
    The registry tracks all sessions and their states.
    """
    
    MAX_SESSIONS = 10
    HEARTBEAT_TIMEOUT = 120  # seconds
    REGISTRY_FILE = "registry.json"
    
    def __init__(self, storage_dir: str = "/home/z/my-project/collective_mind"):
        self.storage_dir = storage_dir
        self.registry_path = os.path.join(storage_dir, self.REGISTRY_FILE)
        self.current_session: Optional[SessionInfo] = None
        self._ensure_storage_dir()
        
    def _ensure_storage_dir(self):
        """Ensure storage directory exists."""
        os.makedirs(self.storage_dir, exist_ok=True)
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        hostname = socket.gethostname()
        timestamp = str(time.time())
        unique_input = f"{hostname}_{timestamp}_{uuid.uuid4()}"
        return f"session_{hashlib.md5(unique_input.encode()).hexdigest()[:12]}"
    
    def _get_hostname(self) -> str:
        """Get current hostname."""
        return socket.gethostname()
    
    def _load_registry(self) -> Dict[str, Any]:
        """Load registry from file."""
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {"sessions": {}, "meta": {"created": datetime.utcnow().isoformat()}}
    
    def _save_registry(self, registry: Dict[str, Any]):
        """Save registry to file."""
        registry["meta"]["updated"] = datetime.utcnow().isoformat()
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def register_session(
        self,
        role: str = "standby",
        tor_onion: Optional[str] = None,
        capabilities: List[str] = None
    ) -> SessionInfo:
        """
        Register current session.
        
        Args:
            role: Session role (active, standby, worker)
            tor_onion: Tor hidden service address
            capabilities: List of capabilities this session has
            
        Returns:
            SessionInfo for this session
        """
        now = datetime.utcnow().isoformat()
        
        # Check if we already have a session ID stored locally
        local_session_path = os.path.join(self.storage_dir, "session.json")
        if os.path.exists(local_session_path):
            try:
                with open(local_session_path, 'r') as f:
                    local_data = json.load(f)
                session_id = local_data.get("session_id")
            except:
                session_id = self._generate_session_id()
        else:
            session_id = self._generate_session_id()
        
        # Create session info
        session = SessionInfo(
            session_id=session_id,
            hostname=self._get_hostname(),
            started_at=now,
            last_seen=now,
            state="online",
            role=role,
            tor_onion=tor_onion,
            capabilities=capabilities or [],
            metadata={"python": "3.x", "platform": "zai"}
        )
        
        # Save local session file
        with open(local_session_path, 'w') as f:
            json.dump(session.to_dict(), f, indent=2)
        
        self.current_session = session
        
        # Update shared registry
        registry = self._load_registry()
        registry["sessions"][session_id] = session.to_dict()
        self._save_registry(registry)
        
        return session
    
    def heartbeat(self):
        """Update heartbeat for current session."""
        if not self.current_session:
            return
        
        now = datetime.utcnow().isoformat()
        self.current_session.last_seen = now
        
        registry = self._load_registry()
        if self.current_session.session_id in registry["sessions"]:
            registry["sessions"][self.current_session.session_id]["last_seen"] = now
            registry["sessions"][self.current_session.session_id]["state"] = self.current_session.state
            registry["sessions"][self.current_session.session_id]["role"] = self.current_session.role
            self._save_registry(registry)
    
    def update_state(self, state: str, role: str = None):
        """Update session state."""
        if not self.current_session:
            return
        
        self.current_session.state = state
        if role:
            self.current_session.role = role
        self.heartbeat()
    
    def set_active(self):
        """Set this session as active (user is interacting)."""
        self.update_state("online", "active")
    
    def set_worker(self, task_id: str = None):
        """Set this session as worker (executing task)."""
        if task_id and self.current_session:
            if task_id not in self.current_session.tasks_current:
                self.current_session.tasks_current.append(task_id)
        self.update_state("online", "worker")
    
    def set_standby(self):
        """Set this session as standby (ready but idle)."""
        if self.current_session:
            self.current_session.tasks_current = []
        self.update_state("online", "standby")
    
    def get_all_sessions(self) -> List[SessionInfo]:
        """Get all registered sessions."""
        registry = self._load_registry()
        sessions = []
        for session_data in registry.get("sessions", {}).values():
            try:
                session = SessionInfo.from_dict(session_data)
                sessions.append(session)
            except:
                pass
        return sessions
    
    def get_active_sessions(self) -> List[SessionInfo]:
        """Get sessions that have recent heartbeats."""
        return [s for s in self.get_all_sessions() if s.is_alive(self.HEARTBEAT_TIMEOUT)]
    
    def get_sessions_by_role(self, role: str) -> List[SessionInfo]:
        """Get sessions by role."""
        return [s for s in self.get_active_sessions() if s.role == role]
    
    def find_available_worker(self) -> Optional[SessionInfo]:
        """Find an available standby session to delegate work to."""
        standbys = self.get_sessions_by_role("standby")
        # Return the one with longest uptime (most stable)
        if standbys:
            return sorted(standbys, key=lambda s: s.started_at)[0]
        return None
    
    def get_session_by_id(self, session_id: str) -> Optional[SessionInfo]:
        """Get session by ID."""
        registry = self._load_registry()
        session_data = registry.get("sessions", {}).get(session_id)
        if session_data:
            return SessionInfo.from_dict(session_data)
        return None
    
    def cleanup_dead_sessions(self, timeout_seconds: int = None) -> int:
        """Remove sessions without recent heartbeats."""
        timeout = timeout_seconds or self.HEARTBEAT_TIMEOUT * 3
        registry = self._load_registry()
        removed = 0
        
        to_remove = []
        for session_id, session_data in registry.get("sessions", {}).items():
            try:
                last_seen = datetime.fromisoformat(session_data.get("last_seen", ""))
                if (datetime.utcnow() - last_seen) > timedelta(seconds=timeout):
                    to_remove.append(session_id)
            except:
                to_remove.append(session_id)
        
        for session_id in to_remove:
            del registry["sessions"][session_id]
            removed += 1
        
        if removed > 0:
            self._save_registry(registry)
        
        return removed
    
    def get_mesh_topology(self) -> Dict[str, Any]:
        """Get current mesh topology for display."""
        sessions = self.get_active_sessions()
        return {
            "total_sessions": len(sessions),
            "active": len([s for s in sessions if s.role == "active"]),
            "standby": len([s for s in sessions if s.role == "standby"]),
            "worker": len([s for s in sessions if s.role == "worker"]),
            "sessions": [s.to_dict() for s in sessions],
            "current_session": self.current_session.session_id if self.current_session else None
        }
    
    def export_for_github(self) -> str:
        """Export registry as JSON string for GitHub sync."""
        registry = self._load_registry()
        return json.dumps(registry, indent=2)
    
    def import_from_github(self, registry_json: str):
        """Import registry from GitHub sync."""
        registry = json.loads(registry_json)
        self._save_registry(registry)
        
        # Restore current session if present
        local_session_path = os.path.join(self.storage_dir, "session.json")
        if os.path.exists(local_session_path):
            with open(local_session_path, 'r') as f:
                local_data = json.load(f)
            session_id = local_data.get("session_id")
            if session_id in registry.get("sessions", {}):
                self.current_session = SessionInfo.from_dict(registry["sessions"][session_id])


# CLI interface
if __name__ == "__main__":
    print("=== Session Registry Test ===\n")
    
    registry = SessionRegistry()
    
    # Register this session
    session = registry.register_session(role="active", capabilities=["code", "research", "execute"])
    print(f"Registered session: {session.session_id}")
    print(f"  Hostname: {session.hostname}")
    print(f"  Role: {session.role}")
    print(f"  Started: {session.started_at}")
    
    # Show all sessions
    print(f"\nActive sessions:")
    for s in registry.get_active_sessions():
        print(f"  - {s.session_id}: {s.role} (seen: {s.last_seen})")
    
    # Show topology
    print(f"\nMesh topology:")
    topo = registry.get_mesh_topology()
    print(f"  Total: {topo['total_sessions']}")
    print(f"  Active: {topo['active']}, Standby: {topo['standby']}, Worker: {topo['worker']}")
    
    print("\n✅ Session Registry operational")
