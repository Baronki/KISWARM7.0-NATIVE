#!/usr/bin/env python3
"""
KISWARM Collective Mind - Task Manager
Delegates and tracks tasks between sessions
"""

import os
import json
import uuid
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict, field
from enum import Enum


class TaskType(Enum):
    """Types of tasks that can be delegated."""
    EXECUTE = "execute"      # Run shell command
    RESEARCH = "research"    # Search and analyze
    CODE = "code"           # Write/modify code
    ANALYZE = "analyze"     # Deep analysis
    SYNC = "sync"           # Sync data
    BACKUP = "backup"       # Backup operation


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class TaskStatus(Enum):
    """Task status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class Task:
    """A delegatable task."""
    task_id: str
    task_type: str
    priority: str
    status: str
    created_by: str
    assigned_to: str  # session_id or "any" or "broadcast"
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    timeout_seconds: int = 300
    payload: Dict[str, Any] = field(default_factory=dict)
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    progress: int = 0  # 0-100
    retries: int = 0
    max_retries: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        return cls(**data)
    
    def is_expired(self) -> bool:
        """Check if task has expired."""
        if self.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
            return False
        if self.started_at:
            started = datetime.fromisoformat(self.started_at)
            return (datetime.utcnow() - started) > timedelta(seconds=self.timeout_seconds)
        return False
    
    def can_retry(self) -> bool:
        """Check if task can be retried."""
        return self.retries < self.max_retries and self.status in (
            TaskStatus.FAILED.value, TaskStatus.TIMEOUT.value
        )


class TaskQueue:
    """
    Local task queue for a session.
    """
    
    QUEUE_FILE = "tasks.json"
    MAX_HISTORY = 100
    
    def __init__(self, storage_dir: str = "/home/z/my-project/collective_mind"):
        self.storage_dir = storage_dir
        self.queue_path = os.path.join(storage_dir, self.QUEUE_FILE)
        self.tasks: Dict[str, Task] = {}
        self._load()
    
    def _load(self):
        """Load tasks from file."""
        if os.path.exists(self.queue_path):
            try:
                with open(self.queue_path, 'r') as f:
                    data = json.load(f)
                for task_data in data.get("tasks", []):
                    task = Task.from_dict(task_data)
                    self.tasks[task.task_id] = task
            except:
                pass
    
    def _save(self):
        """Save tasks to file."""
        data = {
            "tasks": [t.to_dict() for t in self.tasks.values()],
            "meta": {
                "updated": datetime.utcnow().isoformat(),
                "count": len(self.tasks)
            }
        }
        with open(self.queue_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def add(self, task: Task):
        """Add task to queue."""
        self.tasks[task.task_id] = task
        self._save()
    
    def get(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def update(self, task: Task):
        """Update task."""
        self.tasks[task.task_id] = task
        self._save()
    
    def remove(self, task_id: str):
        """Remove task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()
    
    def get_pending(self) -> List[Task]:
        """Get all pending tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.PENDING.value]
    
    def get_running(self) -> List[Task]:
        """Get all running tasks."""
        return [t for t in self.tasks.values() if t.status == TaskStatus.RUNNING.value]
    
    def get_assigned_to(self, session_id: str) -> List[Task]:
        """Get tasks assigned to a specific session."""
        return [
            t for t in self.tasks.values()
            if t.assigned_to == session_id and t.status in (
                TaskStatus.PENDING.value, TaskStatus.QUEUED.value
            )
        ]
    
    def get_broadcast_tasks(self) -> List[Task]:
        """Get broadcast tasks (any session can pick up)."""
        return [
            t for t in self.tasks.values()
            if t.assigned_to == "any" and t.status == TaskStatus.PENDING.value
        ]
    
    def cleanup_completed(self, max_age_hours: int = 24):
        """Remove old completed tasks."""
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        to_remove = []
        
        for task_id, task in self.tasks.items():
            if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
                if task.completed_at:
                    completed = datetime.fromisoformat(task.completed_at)
                    if completed < cutoff:
                        to_remove.append(task_id)
        
        for task_id in to_remove:
            del self.tasks[task_id]
        
        if to_remove:
            self._save()
        
        return len(to_remove)


class TaskManager:
    """
    Manages task delegation between sessions.
    """
    
    # Timeout defaults by task type
    DEFAULT_TIMEOUTS = {
        TaskType.EXECUTE.value: 60,
        TaskType.RESEARCH.value: 300,
        TaskType.CODE.value: 600,
        TaskType.ANALYZE.value: 900,
        TaskType.SYNC.value: 120,
        TaskType.BACKUP.value: 300
    }
    
    def __init__(self, queue: TaskQueue, session_id: str):
        self.queue = queue
        self.session_id = session_id
        self._handlers: Dict[str, Callable] = {}
        self._running_handlers: Dict[str, Any] = {}
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type."""
        self._handlers[task_type] = handler
    
    def create_task(
        self,
        task_type: str,
        payload: Dict[str, Any],
        priority: str = TaskPriority.MEDIUM.value,
        assigned_to: str = "any",
        timeout: int = None
    ) -> Task:
        """
        Create a new task.
        
        Args:
            task_type: Type of task (execute, research, code, etc.)
            payload: Task-specific data
            priority: Priority level
            assigned_to: Target session_id, "any", or "broadcast"
            timeout: Timeout in seconds (uses default if not specified)
            
        Returns:
            Created Task
        """
        task_id = f"task_{uuid.uuid4().hex[:12]}"
        
        if timeout is None:
            timeout = self.DEFAULT_TIMEOUTS.get(task_type, 300)
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING.value,
            created_by=self.session_id,
            assigned_to=assigned_to,
            created_at=datetime.utcnow().isoformat(),
            timeout_seconds=timeout,
            payload=payload
        )
        
        self.queue.add(task)
        return task
    
    def delegate_task(self, task: Task, target_session: str) -> bool:
        """
        Delegate task to a specific session.
        
        Args:
            task: Task to delegate
            target_session: Session ID to delegate to
            
        Returns:
            True if delegation successful
        """
        task.assigned_to = target_session
        task.status = TaskStatus.QUEUED.value
        self.queue.update(task)
        return True
    
    def accept_task(self, task_id: str) -> Optional[Task]:
        """
        Accept a task assigned to this session.
        
        Returns the task if accepted, None if not found or not assignable.
        """
        task = self.queue.get(task_id)
        if not task:
            return None
        
        # Check if task is for us or broadcast
        if task.assigned_to not in (self.session_id, "any"):
            return None
        
        # Check status
        if task.status != TaskStatus.PENDING.value and task.status != TaskStatus.QUEUED.value:
            return None
        
        # Accept task
        task.assigned_to = self.session_id
        task.status = TaskStatus.RUNNING.value
        task.started_at = datetime.utcnow().isoformat()
        self.queue.update(task)
        
        return task
    
    def update_progress(self, task_id: str, progress: int, message: str = None):
        """Update task progress (0-100)."""
        task = self.queue.get(task_id)
        if task:
            task.progress = min(100, max(0, progress))
            if message:
                task.result["progress_message"] = message
            self.queue.update(task)
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None):
        """Mark task as completed."""
        task = self.queue.get(task_id)
        if task:
            task.completed_at = datetime.utcnow().isoformat()
            task.progress = 100
            
            if error:
                task.status = TaskStatus.FAILED.value
                task.error = error
            else:
                task.status = TaskStatus.COMPLETED.value
                if result is not None:
                    task.result["output"] = result
            
            self.queue.update(task)
    
    def fail_task(self, task_id: str, error: str):
        """Mark task as failed."""
        self.complete_task(task_id, error=error)
    
    def retry_task(self, task_id: str) -> Optional[Task]:
        """Retry a failed task."""
        task = self.queue.get(task_id)
        if task and task.can_retry():
            task.status = TaskStatus.PENDING.value
            task.retries += 1
            task.error = None
            task.started_at = None
            self.queue.update(task)
            return task
        return None
    
    def get_my_tasks(self) -> Dict[str, List[Task]]:
        """Get all tasks relevant to this session."""
        return {
            "created": [t for t in self.queue.tasks.values() if t.created_by == self.session_id],
            "assigned": [t for t in self.queue.tasks.values() if t.assigned_to == self.session_id],
            "available": self.queue.get_broadcast_tasks()
        }
    
    def check_timeouts(self) -> List[Task]:
        """Check for timed out tasks and mark them."""
        timed_out = []
        for task in self.queue.tasks.values():
            if task.is_expired():
                task.status = TaskStatus.TIMEOUT.value
                task.error = "Task timed out"
                task.completed_at = datetime.utcnow().isoformat()
                self.queue.update(task)
                timed_out.append(task)
        return timed_out
    
    def execute_task(self, task: Task) -> Any:
        """
        Execute a task using registered handler.
        
        Returns task result.
        """
        handler = self._handlers.get(task.task_type)
        if not handler:
            raise ValueError(f"No handler registered for task type: {task.task_type}")
        
        try:
            result = handler(task.payload)
            self.complete_task(task.task_id, result)
            return result
        except Exception as e:
            self.fail_task(task.task_id, str(e))
            raise
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get status report for dashboard."""
        tasks = list(self.queue.tasks.values())
        return {
            "total": len(tasks),
            "pending": len([t for t in tasks if t.status == TaskStatus.PENDING.value]),
            "running": len([t for t in tasks if t.status == TaskStatus.RUNNING.value]),
            "completed": len([t for t in tasks if t.status == TaskStatus.COMPLETED.value]),
            "failed": len([t for t in tasks if t.status == TaskStatus.FAILED.value]),
            "my_active": len([t for t in tasks if t.assigned_to == self.session_id and t.status == TaskStatus.RUNNING.value])
        }


# Convenience functions for common task types

def create_execute_task(manager: TaskManager, command: str, cwd: str = None, env: Dict = None) -> Task:
    """Create a command execution task."""
    return manager.create_task(
        task_type=TaskType.EXECUTE.value,
        payload={
            "command": command,
            "cwd": cwd,
            "env": env
        },
        timeout=60
    )


def create_research_task(manager: TaskManager, query: str, depth: str = "medium") -> Task:
    """Create a research task."""
    return manager.create_task(
        task_type=TaskType.RESEARCH.value,
        payload={
            "query": query,
            "depth": depth
        },
        timeout=300
    )


def create_code_task(manager: TaskManager, description: str, files: List[str] = None, language: str = None) -> Task:
    """Create a coding task."""
    return manager.create_task(
        task_type=TaskType.CODE.value,
        payload={
            "description": description,
            "files": files or [],
            "language": language
        },
        timeout=600
    )


# CLI interface
if __name__ == "__main__":
    print("=== Task Manager Test ===\n")
    
    queue = TaskQueue()
    manager = TaskManager(queue, "test-session-001")
    
    # Create a test task
    task = manager.create_task(
        task_type="execute",
        payload={"command": "echo 'Hello from task'"},
        priority="high"
    )
    print(f"Created task: {task.task_id}")
    print(f"  Type: {task.task_type}")
    print(f"  Priority: {task.priority}")
    print(f"  Status: {task.status}")
    
    # Get status
    status = manager.get_status_report()
    print(f"\nQueue status:")
    print(f"  Total: {status['total']}")
    print(f"  Pending: {status['pending']}")
    
    print("\n✅ Task Manager operational")
