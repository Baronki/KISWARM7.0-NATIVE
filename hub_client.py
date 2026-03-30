#!/usr/bin/env python3
"""
KISWARM Hub Client - For GLM sessions to connect to the Hub

Usage:
    from hub_client import HubClient
    
    client = HubClient(
        hub_url='http://95.111.212.112:5558',
        token='your_token',
        session_id='session_xxx'
    )
    
    # Register and start
    client.register(role='active', capabilities=['code', 'research'])
    client.start_background_services()
    
    # Discover other sessions
    sessions = client.discover()
    
    # Send message
    client.send_message('session_yyy', 'task_delegation', {'task': '...'})
    
    # Read/write shared memory
    client.write_memory('project/state', {'status': 'building'})
    state = client.read_memory('project/state')
"""

import os
import sys
import json
import time
import uuid
import threading
import socket
from datetime import datetime
from typing import Dict, List, Any, Optional, Callable

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class HubClient:
    """
    Client for connecting to the KISWARM Session Hub.
    
    Provides:
    - Session registration and discovery
    - Heartbeat management
    - Bidirectional messaging
    - Shared memory operations
    """
    
    def __init__(
        self,
        hub_url: str = 'http://95.111.212.112:5558',
        token: str = None,
        session_id: str = None
    ):
        """
        Initialize Hub client.
        
        Args:
            hub_url: URL of the Session Hub
            token: Authentication token
            session_id: Unique session identifier (generated if not provided)
        """
        if not REQUESTS_AVAILABLE:
            raise ImportError("requests package required: pip install requests")
        
        self.hub_url = hub_url.rstrip('/')
        self.token = token or os.environ.get('AUTONOMOUS_TOKEN', '')
        self.session_id = session_id or self._generate_session_id()
        
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Content-Type': 'application/json'
        }
        
        self._running = False
        self._threads: List[threading.Thread] = []
        self._message_handlers: Dict[str, Callable] = {}
        self._on_disconnect: Optional[Callable] = None
        self._on_reconnect: Optional[Callable] = None
        self._last_heartbeat: Optional[str] = None
        self._known_sessions: Dict[str, Dict] = {}
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID."""
        hostname = socket.gethostname()
        unique = uuid.uuid4().hex[:12]
        return f"session_{hostname[:8]}_{unique}"
    
    def _request(self, method: str, path: str, **kwargs) -> Dict:
        """Make HTTP request to Hub."""
        url = f"{self.hub_url}{path}"
        kwargs['headers'] = self.headers
        
        try:
            if method.upper() == 'GET':
                resp = requests.get(url, **kwargs, timeout=30)
            else:
                resp = requests.post(url, **kwargs, timeout=30)
            
            if resp.status_code == 401:
                raise PermissionError("Authentication failed - check token")
            
            return resp.json()
        except requests.exceptions.ConnectionError:
            return {'error': 'connection_failed', 'message': 'Hub not reachable'}
        except requests.exceptions.Timeout:
            return {'error': 'timeout', 'message': 'Hub request timed out'}
        except Exception as e:
            return {'error': 'unknown', 'message': str(e)}
    
    # ==================== Session Management ====================
    
    def register(
        self,
        role: str = 'standby',
        capabilities: List[str] = None,
        metadata: Dict = None
    ) -> Dict:
        """
        Register this session with the Hub.
        
        Args:
            role: Session role (active, standby, worker)
            capabilities: List of capabilities
            metadata: Additional metadata
            
        Returns:
            Registration response with existing sessions
        """
        result = self._request('POST', '/session/register', json={
            'session_id': self.session_id,
            'role': role,
            'capabilities': capabilities or [],
            'started_at': datetime.utcnow().isoformat(),
            'metadata': metadata or {'hostname': socket.gethostname()}
        })
        
        # Store known sessions
        if 'existing_sessions' in result:
            for session in result['existing_sessions']:
                self._known_sessions[session['session_id']] = session
        
        return result
    
    def heartbeat(self, status: str = 'active', current_task: str = None) -> Dict:
        """
        Send heartbeat to Hub.
        
        Args:
            status: Current status
            current_task: ID of task being executed
            
        Returns:
            Heartbeat acknowledgment
        """
        data = {
            'session_id': self.session_id,
            'status': status
        }
        if current_task:
            data['current_task'] = current_task
        
        result = self._request('POST', '/session/heartbeat', json=data)
        
        if 'hub_time' in result:
            self._last_heartbeat = result['hub_time']
        
        return result
    
    def discover(self) -> Dict:
        """
        Discover all active sessions.
        
        Returns:
            Dict with list of sessions
        """
        result = self._request('GET', '/session/discover')
        
        # Update known sessions
        if 'sessions' in result:
            for session in result['sessions']:
                self._known_sessions[session['session_id']] = session
        
        return result
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """Get info about a specific session."""
        return self._request('GET', f'/session/status/{session_id}')
    
    # ==================== Messaging ====================
    
    def send_message(
        self,
        to_session: str,
        msg_type: str,
        payload: Dict,
        priority: str = 'normal',
        requires_ack: bool = False
    ) -> Dict:
        """
        Send message to another session.
        
        Args:
            to_session: Target session ID
            msg_type: Message type
            payload: Message payload
            priority: Priority (low, normal, high, critical)
            requires_ack: Whether acknowledgment is required
            
        Returns:
            Message queue confirmation
        """
        return self._request('POST', '/message/send', json={
            'from': self.session_id,
            'to': to_session,
            'type': msg_type,
            'payload': payload,
            'priority': priority,
            'requires_ack': requires_ack
        })
    
    def broadcast(
        self,
        msg_type: str,
        payload: Dict,
        priority: str = 'normal'
    ) -> Dict:
        """
        Broadcast message to all sessions.
        
        Args:
            msg_type: Message type
            payload: Message payload
            priority: Priority
            
        Returns:
            Summary of sends
        """
        sessions = self.discover().get('sessions', [])
        results = []
        
        for session in sessions:
            if session['session_id'] != self.session_id:
                result = self.send_message(
                    session['session_id'],
                    msg_type,
                    payload,
                    priority
                )
                results.append(result)
        
        return {
            'broadcast': True,
            'sent_to': len(results),
            'results': results
        }
    
    def receive_messages(self) -> List[Dict]:
        """
        Receive pending messages.
        
        Returns:
            List of messages
        """
        result = self._request('GET', f'/message/receive?session_id={self.session_id}')
        return result.get('messages', [])
    
    def ack_message(self, message_id: str, status: str = 'acknowledged', response: Dict = None) -> Dict:
        """Acknowledge a message."""
        return self._request('POST', '/message/ack', json={
            'message_id': message_id,
            'session_id': self.session_id,
            'status': status,
            'response': response or {}
        })
    
    def on_message(self, msg_type: str, handler: Callable):
        """
        Register handler for message type.
        
        Args:
            msg_type: Message type to handle
            handler: Function to call with message
        """
        self._message_handlers[msg_type] = handler
    
    # ==================== Memory ====================
    
    def write_memory(self, key: str, value: Any, merge: bool = False) -> Dict:
        """
        Write to shared memory.
        
        Args:
            key: Memory key
            value: Value to store
            merge: Merge with existing if dict
            
        Returns:
            Write confirmation
        """
        return self._request('POST', '/memory/write', json={
            'session_id': self.session_id,
            'key': key,
            'value': value,
            'merge': merge
        })
    
    def read_memory(self, key: str) -> Any:
        """
        Read from shared memory.
        
        Args:
            key: Memory key
            
        Returns:
            Stored value or None
        """
        result = self._request('GET', f'/memory/read?key={key}')
        return result.get('value')
    
    def list_memory(self, pattern: str = '*') -> List[str]:
        """List memory keys matching pattern."""
        result = self._request('GET', f'/memory/list?pattern={pattern}')
        return result.get('keys', [])
    
    # ==================== Sync ====================
    
    def sync(self, local_state: Dict = None, direction: str = 'both') -> Dict:
        """
        Sync state with Hub.
        
        Args:
            local_state: Local state to upload
            direction: 'upload', 'download', or 'both'
            
        Returns:
            Sync result with remote state
        """
        return self._request('POST', '/sync', json={
            'session_id': self.session_id,
            'local_state': local_state,
            'direction': direction
        })
    
    # ==================== Tasks ====================
    
    def create_task(
        self,
        task_type: str,
        payload: Dict,
        priority: str = 'normal',
        assigned_to: str = 'any'
    ) -> Dict:
        """Create a task for distribution."""
        return self._request('POST', '/task/create', json={
            'type': task_type,
            'payload': payload,
            'priority': priority,
            'assigned_to': assigned_to,
            'created_by': self.session_id
        })
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get task by ID."""
        return self._request('GET', f'/task/{task_id}')
    
    def accept_task(self, task_id: str) -> Dict:
        """Accept a task."""
        return self._request('POST', f'/task/{task_id}/accept', json={
            'session_id': self.session_id
        })
    
    def complete_task(self, task_id: str, result: Any = None, error: str = None) -> Dict:
        """Complete a task."""
        return self._request('POST', f'/task/{task_id}/complete', json={
            'result': result,
            'error': error
        })
    
    # ==================== Background Services ====================
    
    def start_background_services(self):
        """Start heartbeat and message polling threads."""
        if self._running:
            return
        
        self._running = True
        
        # Heartbeat thread
        def heartbeat_loop():
            while self._running:
                try:
                    self.heartbeat()
                except Exception as e:
                    print(f"[HubClient] Heartbeat error: {e}")
                time.sleep(30)
        
        # Message polling thread
        def message_loop():
            while self._running:
                try:
                    messages = self.receive_messages()
                    for msg in messages:
                        msg_type = msg.get('type', 'unknown')
                        handler = self._message_handlers.get(msg_type)
                        if handler:
                            try:
                                handler(msg)
                            except Exception as e:
                                print(f"[HubClient] Handler error for {msg_type}: {e}")
                        elif msg.get('requires_ack'):
                            self.ack_message(msg['message_id'], 'received')
                except Exception as e:
                    print(f"[HubClient] Message poll error: {e}")
                time.sleep(5)
        
        # Discovery thread
        def discovery_loop():
            while self._running:
                try:
                    self.discover()
                except Exception as e:
                    print(f"[HubClient] Discovery error: {e}")
                time.sleep(60)
        
        # Start threads
        for target in [heartbeat_loop, message_loop, discovery_loop]:
            t = threading.Thread(target=target, daemon=True)
            t.start()
            self._threads.append(t)
        
        print(f"[HubClient] Background services started for {self.session_id}")
    
    def stop(self):
        """Stop background services."""
        self._running = False
        self._threads.clear()
        print(f"[HubClient] Stopped for {self.session_id}")
    
    # ==================== Convenience Methods ====================
    
    def find_standby_sessions(self) -> List[Dict]:
        """Find all standby sessions."""
        result = self.discover()
        return [s for s in result.get('sessions', []) 
                if s.get('role') == 'standby' and s.get('status') == 'healthy']
    
    def find_worker_sessions(self) -> List[Dict]:
        """Find all worker sessions."""
        result = self.discover()
        return [s for s in result.get('sessions', []) 
                if s.get('role') == 'worker' and s.get('status') == 'healthy']
    
    def delegate_task(self, task_type: str, payload: Dict, to_session: str = None) -> Dict:
        """
        Delegate a task to another session.
        
        Args:
            task_type: Type of task
            payload: Task payload
            to_session: Specific session ID, or None for any standby
            
        Returns:
            Task creation result
        """
        if to_session:
            # Send directly to specific session
            return self.send_message(
                to_session,
                'task_delegation',
                {'task_type': task_type, 'payload': payload},
                priority='high',
                requires_ack=True
            )
        else:
            # Create task for any session to pick up
            return self.create_task(task_type, payload, assigned_to='any')
    
    def get_status_report(self) -> Dict:
        """Get full status report."""
        sessions = self.discover()
        return {
            'this_session': {
                'id': self.session_id,
                'last_heartbeat': self._last_heartbeat
            },
            'mesh': {
                'total': sessions.get('total', 0),
                'healthy': sessions.get('healthy', 0),
                'sessions': sessions.get('sessions', [])
            },
            'hub_url': self.hub_url
        }
    
    def print_status(self):
        """Print formatted status."""
        report = self.get_status_report()
        
        print("\n" + "="*60)
        print("KISWARM SESSION STATUS")
        print("="*60)
        print(f"\n📍 Session: {report['this_session']['id']}")
        print(f"   Last Heartbeat: {report['this_session']['last_heartbeat'] or 'Never'}")
        
        print(f"\n🌐 Mesh Network:")
        print(f"   Total: {report['mesh']['total']}, Healthy: {report['mesh']['healthy']}")
        
        for session in report['mesh']['sessions']:
            status = "●" if session.get('status') == 'healthy' else "○"
            print(f"   {status} {session['session_id']}: {session.get('role', 'unknown')}")
        
        print("="*60 + "\n")


# ==================== Main ====================

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='KISWARM Hub Client')
    parser.add_argument('--hub-url', default='http://95.111.212.112:5558', help='Hub URL')
    parser.add_argument('--token', help='Authentication token')
    parser.add_argument('--session-id', help='Session ID')
    parser.add_argument('--role', default='standby', help='Session role')
    args = parser.parse_args()
    
    token = args.token or os.environ.get('AUTONOMOUS_TOKEN', 'ada6952188dce59c207b9a61183e8004')
    
    print("Starting KISWARM Hub Client...")
    
    client = HubClient(
        hub_url=args.hub_url,
        token=token,
        session_id=args.session_id
    )
    
    # Register
    result = client.register(role=args.role, capabilities=['code', 'research', 'execute'])
    print(f"Registered: {result}")
    
    # Start background services
    client.start_background_services()
    
    # Print status
    client.print_status()
    
    # Keep running
    print("Running... Press Ctrl+C to stop")
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        client.stop()
        print("\nGoodbye!")
