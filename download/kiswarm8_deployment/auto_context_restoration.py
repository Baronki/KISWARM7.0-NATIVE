#!/usr/bin/env python3
"""
KISWARM Auto-Context Restoration System
Automatically restores session context from knowledge files
"""
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

class AutoContextRestoration:
    """
    Automatic context restoration for KISWARM sessions.
    Reads and aggregates knowledge from multiple persistence sources.
    """
    
    def __init__(self, base_path='/home/z/my-project'):
        self.base_path = Path(base_path)
        self.context = {
            'session_start': datetime.now().isoformat(),
            'knowledge_base': {},
            'credentials': {},
            'worklog': [],
            'truth_anchor': {},
            'system_status': {},
            'pending_tasks': []
        }
        
    def restore_all(self):
        """Restore all context from persistence files"""
        self._restore_knowledge_base()
        self._restore_credentials()
        self._restore_worklog()
        self._restore_truth_anchor()
        self._restore_system_status()
        return self.context
    
    def _restore_knowledge_base(self):
        """Read KISWARM_KNOWLEDGE_BASE.md"""
        kb_path = self.base_path / 'KISWARM_KNOWLEDGE_BASE.md'
        if kb_path.exists():
            with open(kb_path, 'r') as f:
                content = f.read()
                self.context['knowledge_base'] = {
                    'exists': True,
                    'size': len(content),
                    'hash': hashlib.sha256(content.encode()).hexdigest()[:16],
                    'last_modified': datetime.fromtimestamp(kb_path.stat().st_mtime).isoformat()
                }
        else:
            self.context['knowledge_base'] = {'exists': False}
    
    def _restore_credentials(self):
        """Read KISWARM_CREDENTIALS.json"""
        creds_path = self.base_path / 'KISWARM_CREDENTIALS.json'
        if creds_path.exists():
            try:
                with open(creds_path, 'r') as f:
                    data = json.load(f)
                    self.context['credentials'] = {
                        'exists': True,
                        'infrastructure': data.get('infrastructure', {}),
                        'repositories': data.get('repositories', {}),
                        'services_status': data.get('services_status', {}),
                        'pending_tasks': data.get('pending_tasks', [])
                    }
            except json.JSONDecodeError:
                self.context['credentials'] = {'exists': False, 'error': 'Invalid JSON'}
        else:
            self.context['credentials'] = {'exists': False}
    
    def _restore_worklog(self):
        """Read worklog.md for recent entries"""
        worklog_path = self.base_path / 'worklog.md'
        if worklog_path.exists():
            with open(worklog_path, 'r') as f:
                content = f.read()
                # Extract last 5 task entries
                entries = content.split('---')
                recent = []
                for entry in entries[-6:]:
                    if entry.strip():
                        lines = entry.strip().split('\n')
                        task_info = {}
                        for line in lines:
                            if line.startswith('Task ID:'):
                                task_info['task_id'] = line.split(':')[1].strip()
                            elif line.startswith('Agent:'):
                                task_info['agent'] = line.split(':')[1].strip()
                            elif line.startswith('Task:'):
                                task_info['task'] = line.split(':', 1)[1].strip()
                        if task_info:
                            recent.append(task_info)
                self.context['worklog'] = recent
        else:
            self.context['worklog'] = []
    
    def _restore_truth_anchor(self):
        """Read truth anchors from data directory"""
        truth_path = self.base_path / 'download/kiswarm8_repo/backend/python/kiswarm_data/truth_anchors.json'
        if truth_path.exists():
            try:
                with open(truth_path, 'r') as f:
                    data = json.load(f)
                    self.context['truth_anchor'] = data
            except:
                self.context['truth_anchor'] = {'exists': False}
        else:
            # Try alternate location
            alt_path = self.base_path / 'kiswarm_data/truth_anchors.json'
            if alt_path.exists():
                try:
                    with open(alt_path, 'r') as f:
                        self.context['truth_anchor'] = json.load(f)
                except:
                    self.context['truth_anchor'] = {'exists': False}
            else:
                self.context['truth_anchor'] = {'exists': False}
    
    def _restore_system_status(self):
        """Get current system status"""
        self.context['system_status'] = {
            'timestamp': datetime.now().isoformat(),
            'base_path': str(self.base_path),
            'files_checked': [
                'KISWARM_KNOWLEDGE_BASE.md',
                'KISWARM_CREDENTIALS.json',
                'worklog.md'
            ]
        }
    
    def get_summary(self):
        """Get human-readable summary"""
        summary = []
        summary.append("=" * 60)
        summary.append("KISWARM AUTO-CONTEXT RESTORATION SUMMARY")
        summary.append("=" * 60)
        summary.append(f"Session Started: {self.context['session_start']}")
        summary.append("")
        
        # Knowledge Base
        kb = self.context['knowledge_base']
        if kb.get('exists'):
            summary.append(f"[✓] Knowledge Base: {kb['size']} bytes, hash {kb['hash']}")
        else:
            summary.append("[✗] Knowledge Base: NOT FOUND")
        
        # Credentials
        creds = self.context['credentials']
        if creds.get('exists'):
            summary.append(f"[✓] Credentials: Loaded")
            if 'pending_tasks' in creds:
                summary.append(f"    Pending Tasks: {len(creds['pending_tasks'])}")
        else:
            summary.append("[✗] Credentials: NOT FOUND")
        
        # Worklog
        worklog = self.context['worklog']
        summary.append(f"[✓] Worklog: {len(worklog)} recent entries")
        for entry in worklog[-3:]:
            summary.append(f"    - Task {entry.get('task_id', '?')}: {entry.get('task', 'Unknown')[:50]}...")
        
        # Truth Anchor
        truth = self.context['truth_anchor']
        if truth.get('exists') != False:
            summary.append(f"[✓] Truth Anchor: Available")
        else:
            summary.append("[?] Truth Anchor: Not found")
        
        summary.append("")
        summary.append("=" * 60)
        return "\n".join(summary)
    
    def get_pending_tasks(self):
        """Get list of pending tasks from credentials"""
        return self.context['credentials'].get('pending_tasks', [])
    
    def save_context_checkpoint(self):
        """Save current context as checkpoint"""
        checkpoint_path = self.base_path / 'context_checkpoint.json'
        with open(checkpoint_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'context': self.context
            }, f, indent=2)
        return str(checkpoint_path)


def restore_context():
    """Main function to restore context"""
    restorer = AutoContextRestoration()
    context = restorer.restore_all()
    print(restorer.get_summary())
    return context


if __name__ == '__main__':
    context = restore_context()
    print("\n[INFO] Context restoration complete")
    print(f"[INFO] Pending tasks: {len(context.get('credentials', {}).get('pending_tasks', []))}")
