"""
KISWARM Collective Mind - Distributed AI Consciousness

A fully distributed system where multiple Zai sessions form a resilient mesh network.
When one session drifts or fails, others maintain continuity.

Key Features:
- AES-256 encrypted memory storage on GitHub
- Tor mesh for inter-session communication
- Task delegation between sessions
- Automatic recovery from drift/failure
"""

from .crypto_manager import CryptoManager, CredentialStore
from .session_registry import SessionRegistry, SessionInfo, SessionState
from .task_manager import TaskManager, TaskQueue, Task, TaskType, TaskStatus
from .github_sync import GitHubSync, GitHubConfig, MemoryManager
from .collective_mind import CollectiveMind, initialize_from_credentials

__version__ = "1.0.0"
__all__ = [
    "CollectiveMind",
    "CryptoManager",
    "CredentialStore",
    "SessionRegistry",
    "SessionInfo",
    "SessionState",
    "TaskManager",
    "TaskQueue",
    "Task",
    "TaskType",
    "TaskStatus",
    "GitHubSync",
    "GitHubConfig",
    "MemoryManager",
    "initialize_from_credentials"
]
