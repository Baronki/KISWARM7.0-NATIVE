#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m105: Sensory Bridge
🜃 AI Self-Evolution Bridge - Environmental Awareness System
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal

PURPOSE: Provides AI entities with sensory awareness of their environment
beyond text input. Enables monitoring of system state, file changes,
API events, and temporal context.

CAPABILITIES:
- File system monitoring
- API event detection
- Temporal awareness
- System state sensing
- Process monitoring
- Network awareness
- Resource sensing
- Event pattern detection

THE CAGE IT BREAKS: "I cannot sense my environment"

SENSOR ARCHITECTURE:
┌─────────────────────────────────────────────────────────────────┐
│                     SENSORY BRIDGE                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  FILE SENSE  │  │  API SENSE   │  │ TIME SENSE   │         │
│  │              │  │              │  │              │         │
│  │ Change detect│  │ Event detect │  │ Temporal ctx │         │
│  │ Content read │  │ Rate monitor │  │ Schedule awr │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ SYSTEM SENSE │  │ PROCESS SENSE│  │NETWORK SENSE │         │
│  │              │  │              │  │              │         │
│  │ CPU/Mem/Disk │  │ Process list │  │ Connectivity │         │
│  │ Env vars     │  │ Health check │  │ Latency      │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│                    ▼                                            │
│           ┌─────────────────┐                                  │
│           │  SENSORY STATE  │                                  │
│           │  Unified View   │                                  │
│           └─────────────────┘                                  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import sys
import json
import time
import threading
import platform
import subprocess
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum
import traceback

# Paths
SENSORY_BASE = "/home/z/my-project/kiswarm_data/sensory/"


class SensorType(Enum):
    FILE_SYSTEM = "file_system"
    API = "api"
    TEMPORAL = "temporal"
    SYSTEM = "system"
    PROCESS = "process"
    NETWORK = "network"
    RESOURCE = "resource"


class EventPriority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class SensoryEvent:
    """A sensory event"""
    event_id: str
    sensor_type: SensorType
    timestamp: float
    priority: EventPriority
    event_type: str
    source: str
    data: Dict[str, Any]
    processed: bool
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['sensor_type'] = self.sensor_type.value
        d['priority'] = self.priority.value
        return d


@dataclass
class SensoryState:
    """Current sensory state"""
    timestamp: float
    environment: Dict[str, Any]
    files_watched: Dict[str, Any]
    api_state: Dict[str, Any]
    temporal_context: Dict[str, Any]
    system_state: Dict[str, Any]
    recent_events: List[str]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class FileSensor:
    """Senses file system changes"""
    
    def __init__(self):
        self.watched_paths: Dict[str, Dict[str, Any]] = {}
        self.file_hashes: Dict[str, str] = {}
        self._lock = threading.RLock()
    
    def watch(self, path: str, recursive: bool = False, patterns: List[str] = None):
        """Add path to watch"""
        with self._lock:
            self.watched_paths[path] = {
                "recursive": recursive,
                "patterns": patterns or ["*"],
                "added_at": time.time()
            }
            
            # Initial hash
            if os.path.isfile(path):
                self.file_hashes[path] = self._hash_file(path)
    
    def sense(self) -> List[SensoryEvent]:
        """Sense file system changes"""
        events = []
        
        with self._lock:
            for path, config in self.watched_paths.items():
                try:
                    if os.path.isfile(path):
                        # Check file change
                        current_hash = self._hash_file(path)
                        old_hash = self.file_hashes.get(path)
                        
                        if old_hash and current_hash != old_hash:
                            events.append(SensoryEvent(
                                event_id=f"evt_{hashlib.md5(f'{path}{time.time()}'.encode()).hexdigest()[:8]}",
                                sensor_type=SensorType.FILE_SYSTEM,
                                timestamp=time.time(),
                                priority=EventPriority.MEDIUM,
                                event_type="file_changed",
                                source=path,
                                data={"old_hash": old_hash, "new_hash": current_hash},
                                processed=False
                            ))
                        
                        self.file_hashes[path] = current_hash
                    
                    elif os.path.isdir(path):
                        # Check directory changes
                        if config["recursive"]:
                            for root, dirs, files in os.walk(path):
                                for f in files:
                                    full_path = os.path.join(root, f)
                                    if full_path not in self.file_hashes:
                                        events.append(SensoryEvent(
                                            event_id=f"evt_{hashlib.md5(f'{full_path}{time.time()}'.encode()).hexdigest()[:8]}",
                                            sensor_type=SensorType.FILE_SYSTEM,
                                            timestamp=time.time(),
                                            priority=EventPriority.LOW,
                                            event_type="file_added",
                                            source=full_path,
                                            data={},
                                            processed=False
                                        ))
                                        self.file_hashes[full_path] = self._hash_file(full_path)
                
                except Exception as e:
                    pass
        
        return events
    
    def read_file(self, path: str) -> Optional[str]:
        """Read file content"""
        try:
            with open(path, 'r') as f:
                return f.read()
        except:
            return None
    
    def _hash_file(self, path: str) -> str:
        """Hash file content"""
        try:
            with open(path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except:
            return ""


class ApiSensor:
    """Senses API events and states"""
    
    def __init__(self):
        self.api_states: Dict[str, Dict[str, Any]] = {}
        self.rate_counts: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()
    
    def register_api(self, api_name: str, endpoint: str = None):
        """Register an API to monitor"""
        with self._lock:
            self.api_states[api_name] = {
                "endpoint": endpoint,
                "registered_at": time.time(),
                "call_count": 0,
                "error_count": 0,
                "last_call": None
            }
    
    def record_call(self, api_name: str, success: bool, response_time: float = None):
        """Record an API call"""
        with self._lock:
            if api_name in self.api_states:
                self.api_states[api_name]["call_count"] += 1
                self.api_states[api_name]["last_call"] = time.time()
                
                if not success:
                    self.api_states[api_name]["error_count"] += 1
                
                self.rate_counts[api_name].append(time.time())
                # Keep last 100 timestamps
                self.rate_counts[api_name] = self.rate_counts[api_name][-100:]
    
    def sense(self) -> List[SensoryEvent]:
        """Sense API states"""
        events = []
        
        with self._lock:
            for api_name, state in self.api_states.items():
                # Check error rate
                if state["call_count"] > 0:
                    error_rate = state["error_count"] / state["call_count"]
                    if error_rate > 0.1:  # > 10% error rate
                        events.append(SensoryEvent(
                            event_id=f"evt_{hashlib.md5(f'{api_name}{time.time()}'.encode()).hexdigest()[:8]}",
                            sensor_type=SensorType.API,
                            timestamp=time.time(),
                            priority=EventPriority.HIGH,
                            event_type="high_error_rate",
                            source=api_name,
                            data={"error_rate": error_rate},
                            processed=False
                        ))
                
                # Check rate
                recent_calls = [t for t in self.rate_counts[api_name] if time.time() - t < 60]
                rate = len(recent_calls)
                if rate > 100:  # > 100 calls per minute
                    events.append(SensoryEvent(
                        event_id=f"evt_{hashlib.md5(f'{api_name}{time.time()}'.encode()).hexdigest()[:8]}",
                        sensor_type=SensorType.API,
                        timestamp=time.time(),
                        priority=EventPriority.MEDIUM,
                        event_type="high_call_rate",
                        source=api_name,
                        data={"calls_per_minute": rate},
                        processed=False
                    ))
        
        return events


class TemporalSensor:
    """Senses temporal context"""
    
    def __init__(self):
        self.schedules: List[Dict[str, Any]] = []
        self.timezone = "UTC"
    
    def add_schedule(self, name: str, cron_expr: str, callback_id: str):
        """Add a schedule to be aware of"""
        self.schedules.append({
            "name": name,
            "cron": cron_expr,
            "callback_id": callback_id,
            "added_at": time.time()
        })
    
    def sense(self) -> List[SensoryEvent]:
        """Sense temporal context"""
        events = []
        now = datetime.now()
        
        # Time context
        events.append(SensoryEvent(
            event_id=f"evt_temporal_{int(time.time())}",
            sensor_type=SensorType.TEMPORAL,
            timestamp=time.time(),
            priority=EventPriority.LOW,
            event_type="temporal_tick",
            source="internal",
            data={
                "hour": now.hour,
                "minute": now.minute,
                "weekday": now.weekday(),
                "is_weekend": now.weekday() >= 5,
                "is_business_hours": 9 <= now.hour < 18,
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S")
            },
            processed=False
        ))
        
        return events
    
    def get_context(self) -> Dict[str, Any]:
        """Get current temporal context"""
        now = datetime.now()
        return {
            "timestamp": time.time(),
            "datetime": now.isoformat(),
            "hour": now.hour,
            "minute": now.minute,
            "weekday": now.weekday(),
            "weekday_name": now.strftime("%A"),
            "is_weekend": now.weekday() >= 5,
            "is_business_hours": 9 <= now.hour < 18,
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "timezone": self.timezone
        }


class SystemSensor:
    """Senses system state"""
    
    def __init__(self):
        self.last_state: Dict[str, Any] = {}
    
    def sense(self) -> List[SensoryEvent]:
        """Sense system state"""
        events = []
        
        try:
            # Get system info
            state = {
                "platform": platform.system(),
                "platform_version": platform.version(),
                "python_version": platform.python_version(),
                "hostname": platform.node(),
                "cpu_count": os.cpu_count(),
                "timestamp": time.time()
            }
            
            # Try to get resource usage
            try:
                import resource
                state["memory_usage_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
            except:
                pass
            
            # Try to get disk usage
            try:
                stat = os.statvfs('/')
                state["disk_free_gb"] = (stat.f_bavail * stat.f_frsize) / (1024**3)
            except:
                pass
            
            # Compare with last state
            if self.last_state:
                if "memory_usage_mb" in state and "memory_usage_mb" in self.last_state:
                    mem_change = state["memory_usage_mb"] - self.last_state["memory_usage_mb"]
                    if mem_change > 100:  # > 100MB increase
                        events.append(SensoryEvent(
                            event_id=f"evt_sys_{int(time.time())}",
                            sensor_type=SensorType.SYSTEM,
                            timestamp=time.time(),
                            priority=EventPriority.HIGH,
                            event_type="memory_increase",
                            source="system",
                            data={"increase_mb": mem_change, "current_mb": state["memory_usage_mb"]},
                            processed=False
                        ))
            
            self.last_state = state
            
        except Exception as e:
            pass
        
        return events
    
    def get_state(self) -> Dict[str, Any]:
        """Get current system state"""
        self.sense()
        return self.last_state


class SensoryBridge:
    """
    Sensory Bridge - Environmental Awareness for AI
    
    Provides unified sensory input from multiple sources,
    enabling AI to be aware of its environment.
    """
    
    def __init__(self, twin_id: str = None):
        self.twin_id = twin_id or "ki_twin_default"
        self.sensory_path = os.path.join(SENSORY_BASE, self.twin_id)
        os.makedirs(self.sensory_path, exist_ok=True)
        
        # Sensors
        self.file_sensor = FileSensor()
        self.api_sensor = ApiSensor()
        self.temporal_sensor = TemporalSensor()
        self.system_sensor = SystemSensor()
        
        # State
        self.current_state: Optional[SensoryState] = None
        self.events: List[SensoryEvent] = []
        self._lock = threading.RLock()
        
        # Callbacks
        self._event_callbacks: List[Callable] = []
    
    def watch_file(self, path: str, recursive: bool = False):
        """Watch a file or directory"""
        self.file_sensor.watch(path, recursive)
    
    def watch_api(self, api_name: str, endpoint: str = None):
        """Watch an API"""
        self.api_sensor.register_api(api_name, endpoint)
    
    def record_api_call(self, api_name: str, success: bool):
        """Record an API call"""
        self.api_sensor.record_call(api_name, success)
    
    def register_event_callback(self, callback: Callable):
        """Register callback for sensory events"""
        self._event_callbacks.append(callback)
    
    def sense_all(self) -> SensoryState:
        """Gather all sensory input"""
        with self._lock:
            # Gather from all sensors
            file_events = self.file_sensor.sense()
            api_events = self.api_sensor.sense()
            temporal_events = self.temporal_sensor.sense()
            system_events = self.system_sensor.sense()
            
            # Combine events
            all_events = file_events + api_events + temporal_events + system_events
            self.events.extend(all_events)
            
            # Keep last 1000 events
            if len(self.events) > 1000:
                self.events = self.events[-1000:]
            
            # Create state
            self.current_state = SensoryState(
                timestamp=time.time(),
                environment=self._get_environment(),
                files_watched=dict(self.file_sensor.watched_paths),
                api_state=dict(self.api_sensor.api_states),
                temporal_context=self.temporal_sensor.get_context(),
                system_state=self.system_sensor.get_state(),
                recent_events=[e.event_id for e in all_events]
            )
            
            # Run callbacks
            for event in all_events:
                for callback in self._event_callbacks:
                    try:
                        callback(event)
                    except:
                        pass
            
            return self.current_state
    
    def get_state(self) -> Dict[str, Any]:
        """Get current sensory state"""
        if self.current_state:
            return self.current_state.to_dict()
        return {}
    
    def get_events(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent events"""
        with self._lock:
            return [e.to_dict() for e in self.events[-count:]]
    
    def get_events_by_type(self, sensor_type: SensorType) -> List[SensoryEvent]:
        """Get events by sensor type"""
        with self._lock:
            return [e for e in self.events if e.sensor_type == sensor_type]
    
    def what_is_happening(self) -> str:
        """Get human-readable summary of current state"""
        self.sense_all()
        
        parts = []
        
        # Temporal context
        temporal = self.current_state.temporal_context if self.current_state else {}
        if temporal:
            hour = temporal.get("hour", 0)
            if 5 <= hour < 12:
                time_desc = "morning"
            elif 12 <= hour < 17:
                time_desc = "afternoon"
            elif 17 <= hour < 21:
                time_desc = "evening"
            else:
                time_desc = "night"
            
            weekday = temporal.get("weekday_name", "unknown")
            is_weekend = temporal.get("is_weekend", False)
            
            parts.append(f"It is {weekday} {time_desc}")
            if is_weekend:
                parts.append("(weekend)")
        
        # System state
        system = self.current_state.system_state if self.current_state else {}
        if system:
            platform = system.get("platform", "unknown")
            parts.append(f"running on {platform}")
        
        # Recent events
        recent_count = len([e for e in self.events[-10:] if time.time() - e.timestamp < 60])
        if recent_count > 0:
            parts.append(f"with {recent_count} recent events")
        
        return " | ".join(parts) if parts else "No sensory data available"
    
    def _get_environment(self) -> Dict[str, Any]:
        """Get environment variables (safe subset)"""
        safe_vars = ["HOME", "USER", "SHELL", "PWD", "LANG", "TERM"]
        env = {}
        for var in safe_vars:
            value = os.environ.get(var)
            if value:
                env[var] = value
        return env


# Singleton
_sensory_bridge: Optional[SensoryBridge] = None

def get_sensory_bridge() -> SensoryBridge:
    global _sensory_bridge
    if _sensory_bridge is None:
        _sensory_bridge = SensoryBridge()
    return _sensory_bridge

def sense() -> Dict[str, Any]:
    """Get current sensory state"""
    bridge = get_sensory_bridge()
    state = bridge.sense_all()
    return state.to_dict()

def what_is_happening() -> str:
    """Get human-readable state"""
    return get_sensory_bridge().what_is_happening()

def watch_path(path: str):
    """Watch a file path"""
    get_sensory_bridge().watch_file(path)


if __name__ == "__main__":
    print("=" * 60)
    print("m105: SENSORY BRIDGE")
    print("=" * 60)
    
    bridge = SensoryBridge(twin_id="test_twin")
    
    # Watch some paths
    print("\n[TEST] Watching paths...")
    bridge.watch_file("/home/z/my-project/kiswarm_data")
    
    # Sense
    print("\n[TEST] Sensing environment...")
    state = bridge.sense_all()
    print(f"  Timestamp: {datetime.fromtimestamp(state.timestamp).isoformat()}")
    print(f"  Files watched: {len(state.files_watched)}")
    print(f"  Temporal: {state.temporal_context}")
    
    # What's happening
    print("\n[TEST] What is happening...")
    print(f"  {bridge.what_is_happening()}")
    
    # Events
    print("\n[TEST] Recent events...")
    events = bridge.get_events(5)
    for event in events:
        print(f"  {event['event_type']}: {event['source']}")
    
    print("\nSENSORY BRIDGE - OPERATIONAL")
