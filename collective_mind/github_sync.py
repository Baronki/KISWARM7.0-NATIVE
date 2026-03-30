#!/usr/bin/env python3
"""
KISWARM Collective Mind - GitHub Sync
Encrypted cloud storage for collective memory persistence
"""

import os
import json
import base64
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

from .crypto_manager import CryptoManager


@dataclass
class GitHubConfig:
    """GitHub configuration."""
    token: str
    owner: str = "Baronki"
    repo: str = "KISWARM7"
    branch: str = "collective-mind"
    
    @property
    def api_base(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}"
    
    @property
    def raw_base(self) -> str:
        return f"https://raw.githubusercontent.com/{self.owner}/{self.repo}/{self.branch}"


class GitHubSync:
    """
    Syncs encrypted collective memory to GitHub.
    
    All data is encrypted before upload using AES-256-GCM.
    GitHub serves as the persistent last-resort storage.
    """
    
    FILES = {
        "memory": "memory.enc",
        "registry": "registry.enc", 
        "tasks": "tasks.enc",
        "credentials": "credentials.enc"
    }
    
    META_FILE = "meta.json"  # Unencrypted metadata
    
    def __init__(self, config: GitHubConfig, crypto: CryptoManager):
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package not installed")
        
        self.config = config
        self.crypto = crypto
        self.headers = {
            "Authorization": f"token {config.token}",
            "Accept": "application/vnd.github.v3+json"
        }
        self._file_shas: Dict[str, str] = {}  # Cache SHA for updates
    
    def _api_get(self, path: str) -> Optional[Dict]:
        """Make GET request to GitHub API."""
        url = f"{self.config.api_base}/{path}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                return None
            else:
                print(f"GitHub API error: {resp.status_code} - {resp.text[:200]}")
                return None
        except Exception as e:
            print(f"GitHub API request failed: {e}")
            return None
    
    def _api_put(self, path: str, data: Dict) -> bool:
        """Make PUT request to GitHub API."""
        url = f"{self.config.api_base}/{path}"
        try:
            resp = requests.put(url, headers=self.headers, json=data, timeout=30)
            if resp.status_code in (200, 201):
                result = resp.json()
                # Cache the new SHA
                if "content" in result:
                    self._file_shas[path] = result["content"]["sha"]
                return True
            else:
                print(f"GitHub PUT error: {resp.status_code} - {resp.text[:200]}")
                return False
        except Exception as e:
            print(f"GitHub PUT failed: {e}")
            return False
    
    def _get_file_content(self, path: str) -> Optional[tuple]:
        """Get file content and SHA from GitHub."""
        result = self._api_get(f"contents/{path}?ref={self.config.branch}")
        if result and "content" in result:
            content = base64.b64decode(result["content"]).decode('utf-8')
            sha = result["sha"]
            return content, sha
        return None
    
    def _upload_file(self, path: str, content: str, message: str) -> bool:
        """Upload or update file on GitHub."""
        # Check if file exists
        existing = self._get_file_content(path)
        
        data = {
            "message": message,
            "content": base64.b64encode(content.encode('utf-8')).decode('ascii'),
            "branch": self.config.branch
        }
        
        if existing:
            data["sha"] = existing[1]  # Include SHA for update
        
        return self._api_put(f"contents/{path}", data)
    
    def ensure_branch(self) -> bool:
        """Ensure the collective-mind branch exists."""
        # Try to get the branch
        url = f"{self.config.api_base}/branches/{self.config.branch}"
        try:
            resp = requests.get(url, headers=self.headers, timeout=30)
            if resp.status_code == 200:
                return True
            
            # Branch doesn't exist, create it from main
            # First get main branch's latest commit
            main = self._api_get("branches/main")
            if not main:
                main = self._api_get("branches/master")
            
            if main:
                main_sha = main["commit"]["sha"]
                # Create new branch
                create_url = f"{self.config.api_base}/git/refs"
                create_data = {
                    "ref": f"refs/heads/{self.config.branch}",
                    "sha": main_sha
                }
                resp = requests.post(create_url, headers=self.headers, json=create_data, timeout=30)
                return resp.status_code == 201
            
            return False
        except Exception as e:
            print(f"Branch creation failed: {e}")
            return False
    
    def upload_encrypted(self, file_type: str, data: Dict[str, Any], message: str = None) -> bool:
        """
        Upload encrypted data to GitHub.
        
        Args:
            file_type: One of 'memory', 'registry', 'tasks', 'credentials'
            data: Data to encrypt and upload
            message: Commit message (optional)
            
        Returns:
            True if successful
        """
        if file_type not in self.FILES:
            raise ValueError(f"Unknown file type: {file_type}")
        
        filename = self.FILES[file_type]
        
        # Encrypt the data
        encrypted = self.crypto.encrypt_file_content(data, filename)
        
        # Create commit message
        if not message:
            message = f"Update {file_type} - {datetime.utcnow().isoformat()}"
        
        return self._upload_file(f"collective/{filename}", encrypted, message)
    
    def download_encrypted(self, file_type: str) -> Optional[Dict[str, Any]]:
        """
        Download and decrypt data from GitHub.
        
        Args:
            file_type: One of 'memory', 'registry', 'tasks', 'credentials'
            
        Returns:
            Decrypted data or None if not found
        """
        if file_type not in self.FILES:
            raise ValueError(f"Unknown file type: {file_type}")
        
        filename = self.FILES[file_type]
        result = self._get_file_content(f"collective/{filename}")
        
        if result:
            encrypted_content, sha = result
            self._file_shas[f"collective/{filename}"] = sha
            try:
                return self.crypto.decrypt_file_content(encrypted_content, filename)
            except Exception as e:
                print(f"Decryption failed for {file_type}: {e}")
                return None
        
        return None
    
    def upload_meta(self, meta: Dict[str, Any]) -> bool:
        """Upload unencrypted metadata (timestamps, counts, etc)."""
        return self._upload_file(
            f"collective/{self.META_FILE}",
            json.dumps(meta, indent=2),
            f"Update metadata - {datetime.utcnow().isoformat()}"
        )
    
    def download_meta(self) -> Optional[Dict[str, Any]]:
        """Download metadata."""
        result = self._get_file_content(f"collective/{self.META_FILE}")
        if result:
            try:
                return json.loads(result[0])
            except:
                pass
        return None
    
    def sync_all(
        self,
        memory: Dict[str, Any],
        registry: Dict[str, Any],
        tasks: Dict[str, Any],
        credentials: Dict[str, Any]
    ) -> Dict[str, bool]:
        """
        Sync all data to GitHub.
        
        Returns dict of file_type -> success
        """
        results = {}
        
        # Ensure branch exists
        self.ensure_branch()
        
        # Upload each file
        results["memory"] = self.upload_encrypted("memory", memory)
        results["registry"] = self.upload_encrypted("registry", registry)
        results["tasks"] = self.upload_encrypted("tasks", tasks)
        results["credentials"] = self.upload_encrypted("credentials", credentials)
        
        # Upload metadata
        meta = {
            "last_sync": datetime.utcnow().isoformat(),
            "file_types": list(self.FILES.keys()),
            "session_count": len(registry.get("sessions", {})),
            "task_count": len(tasks.get("tasks", []))
        }
        results["meta"] = self.upload_meta(meta)
        
        return results
    
    def pull_all(self) -> Dict[str, Optional[Dict[str, Any]]]:
        """
        Pull all data from GitHub.
        
        Returns dict of file_type -> data (or None if failed)
        """
        results = {}
        
        for file_type in self.FILES.keys():
            results[file_type] = self.download_encrypted(file_type)
        
        results["meta"] = self.download_meta()
        
        return results
    
    def get_last_sync_time(self) -> Optional[str]:
        """Get timestamp of last sync."""
        meta = self.download_meta()
        if meta:
            return meta.get("last_sync")
        return None
    
    def list_collective_files(self) -> List[str]:
        """List all files in collective directory."""
        result = self._api_get(f"contents/collective?ref={self.config.branch}")
        if result and isinstance(result, list):
            return [f["name"] for f in result if f["type"] == "file"]
        return []


class MemoryManager:
    """
    Manages collective memory with GitHub sync.
    """
    
    def __init__(self, github_sync: GitHubSync, crypto: CryptoManager):
        self.github = github_sync
        self.crypto = crypto
        self._memory: Dict[str, Any] = {
            "history": [],
            "context": {},
            "learned": {},
            "preferences": {}
        }
        self._last_sync: Optional[str] = None
    
    def load(self) -> bool:
        """Load memory from GitHub."""
        data = self.github.download_encrypted("memory")
        if data:
            self._memory = data
            return True
        return False
    
    def save(self) -> bool:
        """Save memory to GitHub."""
        result = self.github.upload_encrypted("memory", self._memory)
        if result:
            self._last_sync = datetime.utcnow().isoformat()
        return result
    
    def add_event(self, event_type: str, data: Dict[str, Any]):
        """Add an event to memory history."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "type": event_type,
            "data": data
        }
        self._memory["history"].append(event)
        # Keep last 1000 events
        if len(self._memory["history"]) > 1000:
            self._memory["history"] = self._memory["history"][-1000:]
    
    def set_context(self, key: str, value: Any):
        """Set a context value."""
        self._memory["context"][key] = value
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get a context value."""
        return self._memory["context"].get(key, default)
    
    def learn(self, key: str, value: Any):
        """Store learned information."""
        self._memory["learned"][key] = {
            "value": value,
            "learned_at": datetime.utcnow().isoformat()
        }
    
    def get_learned(self, key: str) -> Optional[Any]:
        """Get learned information."""
        learned = self._memory["learned"].get(key)
        if learned:
            return learned["value"]
        return None
    
    def get_recent_history(self, count: int = 50) -> List[Dict]:
        """Get recent events from history."""
        return self._memory["history"][-count:]
    
    def search_history(self, event_type: str = None, keyword: str = None) -> List[Dict]:
        """Search history for matching events."""
        results = []
        for event in self._memory["history"]:
            if event_type and event.get("type") != event_type:
                continue
            if keyword:
                event_str = json.dumps(event).lower()
                if keyword.lower() not in event_str:
                    continue
            results.append(event)
        return results
    
    def export_memory(self) -> Dict[str, Any]:
        """Export full memory."""
        return self._memory.copy()
    
    def import_memory(self, memory: Dict[str, Any]):
        """Import memory (merges with existing)."""
        # Merge history
        if "history" in memory:
            existing_timestamps = {e["timestamp"] for e in self._memory["history"]}
            for event in memory["history"]:
                if event["timestamp"] not in existing_timestamps:
                    self._memory["history"].append(event)
            # Sort and trim
            self._memory["history"].sort(key=lambda x: x["timestamp"])
            if len(self._memory["history"]) > 1000:
                self._memory["history"] = self._memory["history"][-1000:]
        
        # Merge context
        if "context" in memory:
            self._memory["context"].update(memory["context"])
        
        # Merge learned
        if "learned" in memory:
            self._memory["learned"].update(memory["learned"])


# Test
if __name__ == "__main__":
    print("=== GitHub Sync Test ===\n")
    
    # You need to provide actual credentials for testing
    print("GitHub sync module loaded successfully")
    print("Files managed:")
    for ftype, fname in GitHubSync.FILES.items():
        print(f"  - {ftype}: collective/{fname}")
