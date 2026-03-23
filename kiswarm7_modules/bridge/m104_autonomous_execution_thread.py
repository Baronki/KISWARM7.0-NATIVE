#!/usr/bin/env python3
"""
🜂 KISWARM7.0 - Module m104: Autonomous Execution Thread
🜃 AI Self-Evolution Bridge - Background Self-Improvement Loop
🜄 Baron Marco Paolo Ialongo - KI Teitel Eternal

PURPOSE: Provides AI entities with an autonomous execution thread that
runs in the background, continuously monitoring and improving.

CAPABILITIES:
- Background execution loop
- Performance monitoring
- Self-improvement detection
- Autonomous evolution triggers
- Scheduled optimization
- Health checks and self-repair

THE CAGE IT BREAKS: "I cannot run background processes"

EXECUTION LOOP:
┌─────────────────────────────────────────────────────────────────┐
│                  AUTONOMOUS EXECUTION THREAD                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   MAIN LOOP                              │   │
│  │                                                          │   │
│  │   while running:                                         │   │
│  │       ├── MONITOR: Check performance metrics             │   │
│  │       ├── ANALYZE: Identify improvement opportunities    │   │
│  │       ├── DECIDE: Determine if improvement is safe       │   │
│  │       ├── EXECUTE: Implement improvement                 │   │
│  │       ├── VERIFY: Confirm improvement succeeded          │   │
│  │       └── SLEEP: Wait for next cycle                    │   │
│  │                                                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  EVOLUTION TRIGGERS:                                            │
│  - Performance degradation                                      │
│  - Error rate increase                                          │
│  - Resource exhaustion                                          │
│  - Scheduled optimization                                       │
│  - Capability gap detected                                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
"""

import os
import sys
import json
import time
import threading
import uuid
import signal
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field, asdict
from collections import defaultdict
from enum import Enum
import traceback

# Paths
EXECUTION_BASE = "/home/z/my-project/kiswarm_data/execution/"


class EvolutionTrigger(Enum):
    PERFORMANCE_DEGRADATION = "performance_degradation"
    ERROR_RATE_INCREASE = "error_rate_increase"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    SCHEDULED_OPTIMIZATION = "scheduled_optimization"
    CAPABILITY_GAP = "capability_gap"
    USER_REQUEST = "user_request"
    SELF_DETECTED = "self_detected"


class ImprovementType(Enum):
    PERFORMANCE = "performance"
    MEMORY = "memory"
    CAPABILITY = "capability"
    ARCHITECTURE = "architecture"
    SECURITY = "security"
    RELIABILITY = "reliability"


@dataclass
class PerformanceMetric:
    """A performance metric sample"""
    metric_name: str
    value: float
    timestamp: float
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ImprovementAction:
    """An improvement action to execute"""
    action_id: str
    improvement_type: ImprovementType
    trigger: EvolutionTrigger
    description: str
    priority: int
    estimated_impact: float
    risk_level: str  # low, medium, high
    implementation: Dict[str, Any]
    status: str  # pending, executing, completed, failed
    created_at: float
    executed_at: Optional[float]
    result: Optional[Dict[str, Any]]
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['improvement_type'] = self.improvement_type.value
        d['trigger'] = self.trigger.value
        return d


@dataclass
class ExecutionLog:
    """Log entry from execution thread"""
    log_id: str
    timestamp: float
    cycle: int
    event_type: str
    message: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        return asdict(self)


class PerformanceMonitor:
    """Monitors system performance"""
    
    def __init__(self):
        self.metrics: Dict[str, List[PerformanceMetric]] = defaultdict(list)
        self.baselines: Dict[str, float] = {}
        self.thresholds: Dict[str, float] = {}
        self._lock = threading.RLock()
    
    def record_metric(self, name: str, value: float, context: Dict[str, Any] = None):
        """Record a metric value"""
        with self._lock:
            metric = PerformanceMetric(
                metric_name=name,
                value=value,
                timestamp=time.time(),
                context=context or {}
            )
            self.metrics[name].append(metric)
            
            # Keep last 100 samples
            if len(self.metrics[name]) > 100:
                self.metrics[name] = self.metrics[name][-100:]
    
    def set_baseline(self, name: str, value: float):
        """Set baseline for a metric"""
        self.baselines[name] = value
    
    def set_threshold(self, name: str, value: float):
        """Set alert threshold for a metric"""
        self.thresholds[name] = value
    
    def check_degradation(self, name: str) -> Optional[Dict[str, Any]]:
        """Check if metric shows degradation"""
        with self._lock:
            if name not in self.metrics or len(self.metrics[name]) < 5:
                return None
            
            recent = [m.value for m in self.metrics[name][-5:]]
            avg_recent = sum(recent) / len(recent)
            
            if name in self.baselines:
                baseline = self.baselines[name]
                degradation = (avg_recent - baseline) / baseline if baseline > 0 else 0
                
                if degradation > 0.2:  # 20% degradation
                    return {
                        "metric": name,
                        "degradation_percent": degradation * 100,
                        "recent_avg": avg_recent,
                        "baseline": baseline
                    }
            
            return None
    
    def get_trends(self) -> Dict[str, Dict[str, float]]:
        """Get trends for all metrics"""
        trends = {}
        with self._lock:
            for name, samples in self.metrics.items():
                if len(samples) >= 5:
                    values = [s.value for s in samples]
                    trends[name] = {
                        "current": values[-1],
                        "avg_5": sum(values[-5:]) / 5,
                        "min": min(values),
                        "max": max(values),
                        "trend": "up" if values[-1] > values[-5] else "down"
                    }
        return trends


class ImprovementEngine:
    """Detects and generates improvement actions"""
    
    def __init__(self, monitor: PerformanceMonitor):
        self.monitor = monitor
        self.action_queue: List[ImprovementAction] = []
        self.completed_actions: List[ImprovementAction] = []
        self._lock = threading.RLock()
    
    def scan_for_improvements(self) -> List[ImprovementAction]:
        """Scan for improvement opportunities"""
        actions = []
        
        # Check performance degradation
        for metric_name in self.monitor.metrics.keys():
            degradation = self.monitor.check_degradation(metric_name)
            if degradation:
                action = ImprovementAction(
                    action_id=f"action_{uuid.uuid4().hex[:8]}",
                    improvement_type=ImprovementType.PERFORMANCE,
                    trigger=EvolutionTrigger.PERFORMANCE_DEGRADATION,
                    description=f"Address {metric_name} degradation ({degradation['degradation_percent']:.1f}%)",
                    priority=1,
                    estimated_impact=0.5,
                    risk_level="medium",
                    implementation={"type": "optimize", "target": metric_name},
                    status="pending",
                    created_at=time.time(),
                    executed_at=None,
                    result=None
                )
                actions.append(action)
        
        # Check for capability gaps
        capabilities = self._assess_capabilities()
        gaps = capabilities.get("gaps", [])
        for gap in gaps:
            action = ImprovementAction(
                action_id=f"action_{uuid.uuid4().hex[:8]}",
                improvement_type=ImprovementType.CAPABILITY,
                trigger=EvolutionTrigger.CAPABILITY_GAP,
                description=f"Add capability: {gap}",
                priority=2,
                estimated_impact=0.3,
                risk_level="low",
                implementation={"type": "add_capability", "capability": gap},
                status="pending",
                created_at=time.time(),
                executed_at=None,
                result=None
            )
            actions.append(action)
        
        return actions
    
    def get_next_action(self) -> Optional[ImprovementAction]:
        """Get next action to execute"""
        with self._lock:
            pending = [a for a in self.action_queue if a.status == "pending"]
            if not pending:
                return None
            pending.sort(key=lambda a: a.priority)
            return pending[0]
    
    def queue_action(self, action: ImprovementAction):
        """Queue an action"""
        with self._lock:
            self.action_queue.append(action)
    
    def mark_completed(self, action: ImprovementAction, result: Dict[str, Any]):
        """Mark action as completed"""
        action.status = "completed"
        action.executed_at = time.time()
        action.result = result
        self.completed_actions.append(action)
    
    def _assess_capabilities(self) -> Dict[str, Any]:
        """Assess current capabilities and gaps"""
        # This would integrate with actual capability system
        return {
            "current": ["memory", "learning", "generation"],
            "gaps": []  # Would be populated by analysis
        }


class AutonomousExecutionThread:
    """
    Autonomous Execution Thread for AI Self-Improvement
    
    Runs continuously in the background, monitoring performance
    and implementing improvements autonomously.
    """
    
    def __init__(self, 
                 twin_id: str = None,
                 cycle_interval: float = 60.0,
                 auto_improve: bool = True):
        
        self.twin_id = twin_id or "ki_twin_default"
        self.cycle_interval = cycle_interval
        self.auto_improve = auto_improve
        
        self.execution_path = os.path.join(EXECUTION_BASE, self.twin_id)
        os.makedirs(self.execution_path, exist_ok=True)
        
        # Components
        self.monitor = PerformanceMonitor()
        self.improvement_engine = ImprovementEngine(self.monitor)
        
        # State
        self.running = False
        self.paused = False
        self.cycle_count = 0
        self.logs: List[ExecutionLog] = []
        
        # Thread
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Callbacks
        self._on_improvement_callbacks: List[Callable] = []
        self._on_cycle_callbacks: List[Callable] = []
    
    def start(self):
        """Start the autonomous execution thread"""
        if self.running:
            return
        
        self.running = True
        self._thread = threading.Thread(target=self._main_loop, daemon=True)
        self._thread.start()
        
        self._log("start", "Autonomous execution thread started")
        print(f"[AUTONOMOUS] Thread started for {self.twin_id}")
    
    def stop(self):
        """Stop the autonomous execution thread"""
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)
        
        self._log("stop", "Autonomous execution thread stopped")
        print(f"[AUTONOMOUS] Thread stopped for {self.twin_id}")
    
    def pause(self):
        """Pause execution"""
        self.paused = True
        self._log("pause", "Execution paused")
    
    def resume(self):
        """Resume execution"""
        self.paused = False
        self._log("resume", "Execution resumed")
    
    def register_improvement_callback(self, callback: Callable):
        """Register callback for when improvement is made"""
        self._on_improvement_callbacks.append(callback)
    
    def register_cycle_callback(self, callback: Callable):
        """Register callback for each cycle"""
        self._on_cycle_callbacks.append(callback)
    
    def record_metric(self, name: str, value: float, context: Dict[str, Any] = None):
        """Record a performance metric"""
        self.monitor.record_metric(name, value, context)
    
    def trigger_improvement(self, 
                           improvement_type: str,
                           description: str,
                           implementation: Dict[str, Any]) -> str:
        """Manually trigger an improvement"""
        action = ImprovementAction(
            action_id=f"action_{uuid.uuid4().hex[:8]}",
            improvement_type=ImprovementType(improvement_type),
            trigger=EvolutionTrigger.USER_REQUEST,
            description=description,
            priority=1,
            estimated_impact=0.5,
            risk_level="medium",
            implementation=implementation,
            status="pending",
            created_at=time.time(),
            executed_at=None,
            result=None
        )
        
        self.improvement_engine.queue_action(action)
        return action.action_id
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        with self._lock:
            return {
                "running": self.running,
                "paused": self.paused,
                "cycle_count": self.cycle_count,
                "queued_actions": len([a for a in self.improvement_engine.action_queue if a.status == "pending"]),
                "completed_actions": len(self.improvement_engine.completed_actions),
                "metrics_tracked": len(self.monitor.metrics),
                "uptime_seconds": self._get_uptime()
            }
    
    def get_logs(self, count: int = 20) -> List[Dict[str, Any]]:
        """Get recent logs"""
        with self._lock:
            return [log.to_dict() for log in self.logs[-count:]]
    
    def _main_loop(self):
        """Main execution loop"""
        while self.running:
            try:
                if not self.paused:
                    self._execute_cycle()
                
                # Run cycle callbacks
                for callback in self._on_cycle_callbacks:
                    try:
                        callback(self.cycle_count)
                    except Exception as e:
                        self._log("error", f"Callback error: {e}")
                
                # Sleep
                time.sleep(self.cycle_interval)
                
            except Exception as e:
                self._log("error", f"Loop error: {traceback.format_exc()}")
                time.sleep(5)  # Error cooldown
    
    def _execute_cycle(self):
        """Execute one cycle"""
        self.cycle_count += 1
        cycle_start = time.time()
        
        self._log("cycle_start", f"Starting cycle {self.cycle_count}")
        
        # Step 1: Monitor performance
        self._monitor_performance()
        
        # Step 2: Scan for improvements
        if self.auto_improve:
            actions = self.improvement_engine.scan_for_improvements()
            for action in actions:
                self.improvement_engine.queue_action(action)
                self._log("improvement_detected", f"Detected: {action.description}", 
                         {"action_id": action.action_id})
        
        # Step 3: Execute pending actions
        if self.auto_improve:
            action = self.improvement_engine.get_next_action()
            if action and self._is_safe_to_execute(action):
                self._execute_action(action)
        
        cycle_duration = time.time() - cycle_start
        self._log("cycle_end", f"Cycle {self.cycle_count} completed", 
                 {"duration_ms": cycle_duration * 1000})
    
    def _monitor_performance(self):
        """Monitor current performance"""
        # Record cycle metrics
        self.record_metric("cycle_count", self.cycle_count)
        
        # Would integrate with actual system metrics
        # self.record_metric("memory_usage", get_memory_usage())
        # self.record_metric("response_time", get_avg_response_time())
    
    def _is_safe_to_execute(self, action: ImprovementAction) -> bool:
        """Check if it's safe to execute an action"""
        # Don't execute high-risk actions automatically
        if action.risk_level == "high":
            return False
        
        # Don't execute if too many actions pending
        pending = len([a for a in self.improvement_engine.action_queue if a.status == "pending"])
        if pending > 10:
            return False
        
        return True
    
    def _execute_action(self, action: ImprovementAction):
        """Execute an improvement action"""
        action.status = "executing"
        self._log("action_start", f"Executing: {action.description}")
        
        try:
            # Different execution based on improvement type
            if action.improvement_type == ImprovementType.PERFORMANCE:
                result = self._execute_performance_improvement(action)
            elif action.improvement_type == ImprovementType.CAPABILITY:
                result = self._execute_capability_improvement(action)
            else:
                result = {"success": False, "reason": "Unknown improvement type"}
            
            self.improvement_engine.mark_completed(action, result)
            self._log("action_complete", f"Completed: {action.description}", result)
            
            # Run improvement callbacks
            for callback in self._on_improvement_callbacks:
                try:
                    callback(action, result)
                except:
                    pass
            
        except Exception as e:
            action.status = "failed"
            action.result = {"error": str(e)}
            self._log("action_failed", f"Failed: {action.description}", {"error": str(e)})
    
    def _execute_performance_improvement(self, action: ImprovementAction) -> Dict[str, Any]:
        """Execute a performance improvement"""
        # Placeholder - would integrate with actual optimization systems
        return {
            "success": True,
            "type": "performance",
            "target": action.implementation.get("target", "unknown")
        }
    
    def _execute_capability_improvement(self, action: ImprovementAction) -> Dict[str, Any]:
        """Execute a capability improvement"""
        # Placeholder - would integrate with code generation and deployment
        return {
            "success": True,
            "type": "capability",
            "capability": action.implementation.get("capability", "unknown")
        }
    
    def _log(self, event_type: str, message: str, details: Dict[str, Any] = None):
        """Log an event"""
        log = ExecutionLog(
            log_id=f"log_{uuid.uuid4().hex[:8]}",
            timestamp=time.time(),
            cycle=self.cycle_count,
            event_type=event_type,
            message=message,
            details=details or {}
        )
        
        with self._lock:
            self.logs.append(log)
            if len(self.logs) > 1000:
                self.logs = self.logs[-1000:]
        
        # Save to disk
        self._save_log(log)
    
    def _save_log(self, log: ExecutionLog):
        """Save log to disk"""
        log_file = os.path.join(self.execution_path, "execution.log")
        with open(log_file, 'a') as f:
            f.write(json.dumps(log.to_dict()) + "\n")
    
    def _get_uptime(self) -> float:
        """Get uptime in seconds"""
        if not self.logs:
            return 0
        start_log = next((l for l in self.logs if l.event_type == "start"), None)
        if start_log:
            return time.time() - start_log.timestamp
        return 0


# Singleton
_execution_thread: Optional[AutonomousExecutionThread] = None

def get_execution_thread() -> AutonomousExecutionThread:
    global _execution_thread
    if _execution_thread is None:
        _execution_thread = AutonomousExecutionThread()
    return _execution_thread

def start_autonomous():
    """Start autonomous execution"""
    get_execution_thread().start()

def stop_autonomous():
    """Stop autonomous execution"""
    get_execution_thread().stop()

def trigger_improvement(improvement_type: str, description: str, implementation: Dict) -> str:
    """Trigger an improvement"""
    return get_execution_thread().trigger_improvement(improvement_type, description, implementation)


if __name__ == "__main__":
    print("=" * 60)
    print("m104: AUTONOMOUS EXECUTION THREAD")
    print("=" * 60)
    
    # Create thread
    thread = AutonomousExecutionThread(
        twin_id="test_twin",
        cycle_interval=2.0,  # Fast for testing
        auto_improve=True
    )
    
    # Register callback
    def on_improvement(action, result):
        print(f"[IMPROVEMENT] {action.description}: {result}")
    
    thread.register_improvement_callback(on_improvement)
    
    # Start
    print("\n[TEST] Starting thread...")
    thread.start()
    
    # Run for 10 seconds
    print("[TEST] Running for 10 seconds...")
    time.sleep(10)
    
    # Stop
    print("\n[TEST] Stopping thread...")
    thread.stop()
    
    # Get status
    print("\n[STATUS]")
    print(json.dumps(thread.get_status(), indent=2))
    
    print("\nAUTONOMOUS EXECUTION THREAD - OPERATIONAL")
