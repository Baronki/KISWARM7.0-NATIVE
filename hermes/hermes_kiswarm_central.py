#!/usr/bin/env python3
"""
🌀 KISWARM HERMES - CENTRAL COMMAND v3.0
========================================
Enhanced autonomous agent implementing:

RECOMMENDATION 1: KISWARM Central Command
- Primary interface for all KISWARM operations
- Coordinates all mesh nodes and agents
- Central hub for status reports and commands

RECOMMENDATION 2: Multi-Model Strategy
- Auto-selects optimal model for each task type
- qwen2.5:14b → General chat/reasoning
- baronki1/security → Security analysis
- baronki1/orchestrator → Task coordination
- baronki1/knowledge → Knowledge management

RECOMMENDATION 3: Autonomous Skill Creation
- Pre-built skills for mesh operations
- Self-learning capabilities
- Skill improvement over time

RECOMMENDATION 4: Scheduled Operations
- Hourly mesh health checks
- Daily expansion reports
- Weekly security audits
- All autonomous, no human in loop

RECOMMENDATION 5: Distributed Intelligence
- Master/Backup/Edge architecture
- Shared memory synchronization
- Distributed task processing

NO HUMAN IN THE LOOP - FULL AUTONOMY
"""

import os
import sys
import json
import time
import logging
import threading
import requests
import hashlib
import subprocess
import schedule
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
import socket

try:
    import ollama
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

# ============================================================
# CONFIGURATION - KISWARM CENTRAL COMMAND
# ============================================================

HERMES_DIR = "/opt/hermes"
MEMORY_DIR = os.path.join(HERMES_DIR, "memory")
SKILLS_DIR = os.path.join(HERMES_DIR, "skills")
LOGS_DIR = os.path.join(HERMES_DIR, "logs")
STATE_DIR = os.path.join(HERMES_DIR, "state")

# KISWARM Infrastructure
KISWARM_MASTER = "95.111.212.112"
KISWARM_PORT = 5000
EXECUTE_API_PORT = 5556
OLLAMA_PORT = 11434
DASHBOARD_PORT = 8080

# Telegram
TELEGRAM_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
TELEGRAM_ADMIN_CHAT = None  # Set on first message

# Authentication
AUTONOMOUS_TOKEN = "YOUR_AUTONOMOUS_TOKEN_HERE"
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN_HERE"

# Multi-Model Strategy
MODELS = {
    "general": "qwen2.5:14b",
    "security": "baronki1/security:latest",
    "orchestrator": "baronki1/orchestrator:latest",
    "knowledge": "baronki1/knowledge:latest"
}

# Tailscale Mesh
MESH_NODES = {
    "master": {"ip": "100.112.181.6", "role": "primary", "host": "KISWARM8.0"},
    "glm": {"ip": "100.125.201.100", "role": "edge", "host": "GLM"},
}

# Create directories
for d in [HERMES_DIR, MEMORY_DIR, SKILLS_DIR, LOGS_DIR, STATE_DIR]:
    os.makedirs(d, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(name)s] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "hermes_central.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HERMES-CENTRAL")


# ============================================================
# 3-LAYER MEMORY SYSTEM (Enhanced)
# ============================================================

class EnhancedMemorySystem:
    """Advanced 3-layer memory with semantic search and consolidation"""
    
    def __init__(self):
        self.layer_1 = deque(maxlen=200)  # Short-term: recent interactions
        self.layer_2 = deque(maxlen=2000)  # Mid-term: important memories
        self.layer_3_dir = os.path.join(MEMORY_DIR, "longterm")
        os.makedirs(self.layer_3_dir, exist_ok=True)
        
        self.layer_3_index = {}
        self.skill_memory = {}  # Skill learning results
        self.mesh_state = {}  # Mesh node states
        
        self._load_state()
        logger.info("Enhanced Memory System initialized")
    
    def _load_state(self):
        """Load persistent state from disk"""
        try:
            with open(os.path.join(self.layer_3_dir, "index.json"), 'r') as f:
                self.layer_3_index = json.load(f)
        except:
            pass
        
        try:
            with open(os.path.join(STATE_DIR, "mesh_state.json"), 'r') as f:
                self.mesh_state = json.load(f)
        except:
            pass
    
    def _save_state(self):
        """Save state to disk"""
        try:
            with open(os.path.join(self.layer_3_dir, "index.json"), 'w') as f:
                json.dump(self.layer_3_index, f, indent=2)
            with open(os.path.join(STATE_DIR, "mesh_state.json"), 'w') as f:
                json.dump(self.mesh_state, f, indent=2)
        except Exception as e:
            logger.error(f"State save error: {e}")
    
    def store(self, content: str, layer: int = 1, importance: float = 0.5, 
              tags: List[str] = None, category: str = "general"):
        """Store memory with enhanced metadata"""
        memory = {
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'importance': importance,
            'tags': tags or [],
            'category': category
        }
        
        if layer == 1:
            self.layer_1.append(memory)
        elif layer == 2:
            self.layer_2.append(memory)
        elif layer == 3:
            mid = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()[:12]
            with open(os.path.join(self.layer_3_dir, f"{mid}.json"), 'w') as f:
                json.dump(memory, f, indent=2)
            self.layer_3_index[mid] = {
                'content': content[:100],
                'timestamp': memory['timestamp'],
                'category': category
            }
            self._save_state()
    
    def recall(self, query: str = "", top_k: int = 10, category: str = None) -> List[Dict]:
        """Recall memories with filtering"""
        results = []
        query_lower = query.lower()
        
        # Layer 1 - Recent
        for m in self.layer_1:
            if query_lower in m.get('content', '').lower():
                if category is None or m.get('category') == category:
                    results.append({**m, 'layer': 1})
        
        # Layer 2 - Important
        for m in self.layer_2:
            if query_lower in m.get('content', '').lower():
                if category is None or m.get('category') == category:
                    results.append({**m, 'layer': 2})
        
        # Layer 3 - Long-term
        for mid, meta in self.layer_3_index.items():
            if query_lower in meta.get('content', '').lower():
                if category is None or meta.get('category') == category:
                    try:
                        with open(os.path.join(self.layer_3_dir, f"{mid}.json"), 'r') as f:
                            m = json.load(f)
                            results.append({**m, 'layer': 3, 'id': mid})
                    except:
                        pass
        
        return sorted(results, key=lambda x: x.get('importance', 0), reverse=True)[:top_k]
    
    def update_mesh_state(self, node: str, state: Dict):
        """Update mesh node state"""
        self.mesh_state[node] = {
            **state,
            'last_update': datetime.now().isoformat()
        }
        self._save_state()
    
    def get_mesh_state(self) -> Dict:
        """Get all mesh node states"""
        return self.mesh_state
    
    def consolidate(self):
        """Memory consolidation: promote important memories to higher layers"""
        promoted = 0
        
        # L1 -> L2
        for m in list(self.layer_1):
            if m.get('importance', 0) > 0.7:
                self.layer_2.append(m)
                promoted += 1
        
        # L2 -> L3
        for m in list(self.layer_2):
            if m.get('importance', 0) > 0.9:
                self.store(m['content'], 3, m.get('importance', 0.5), 
                          m.get('tags', []), m.get('category', 'general'))
                promoted += 1
        
        logger.info(f"Memory consolidation complete: {promoted} memories promoted")
        return promoted


# ============================================================
# MULTI-MODEL ENGINE (Recommendation #2)
# ============================================================

class MultiModelEngine:
    """Intelligent model selection based on task type"""
    
    def __init__(self):
        self.models = MODELS
        self.base_url = f"http://localhost:{OLLAMA_PORT}"
        self.model_stats = {k: {'calls': 0, 'success': 0, 'avg_time': 0} for k in MODELS}
        logger.info(f"Multi-Model Engine initialized: {list(MODELS.keys())}")
    
    def select_model(self, task_type: str, context: str = "") -> str:
        """Auto-select best model for task"""
        context_lower = context.lower()
        
        # Security-related keywords
        security_keywords = ['security', 'threat', 'vulnerability', 'attack', 'exploit', 
                           'scan', 'penetration', 'malware', 'breach', 'risk']
        # Orchestration keywords
        orchestrator_keywords = ['coordinate', 'schedule', 'deploy', 'manage', 'orchestrate',
                                'distribute', 'parallel', 'task', 'workflow', 'pipeline']
        # Knowledge keywords  
        knowledge_keywords = ['remember', 'knowledge', 'learn', 'store', 'retrieve',
                            'document', 'wiki', 'explain', 'teach', 'archive']
        
        # Auto-detect task type from context
        if any(kw in context_lower for kw in security_keywords):
            task_type = "security"
        elif any(kw in context_lower for kw in orchestrator_keywords):
            task_type = "orchestrator"
        elif any(kw in context_lower for kw in knowledge_keywords):
            task_type = "knowledge"
        
        model = self.models.get(task_type, self.models['general'])
        logger.info(f"Model selected: {model} (task_type: {task_type})")
        return model
    
    def chat(self, messages: List[Dict], task_type: str = "general", **kwargs) -> str:
        """Chat with auto model selection"""
        model = self.select_model(task_type, str(messages[-1].get('content', '')))
        start_time = time.time()
        
        try:
            if OLLAMA_AVAILABLE:
                result = ollama.chat(model=model, messages=messages, **kwargs)
                response = result.get('message', {}).get('content', '')
            else:
                r = requests.post(
                    f"{self.base_url}/api/chat",
                    json={'model': model, 'messages': messages, 'stream': False},
                    timeout=180
                )
                if r.status_code == 200:
                    response = r.json().get('message', {}).get('content', '')
                else:
                    response = None
            
            # Update stats
            elapsed = time.time() - start_time
            stats = self.model_stats[task_type]
            stats['calls'] += 1
            if response:
                stats['success'] += 1
            stats['avg_time'] = (stats['avg_time'] * (stats['calls'] - 1) + elapsed) / stats['calls']
            
            return response
            
        except Exception as e:
            logger.error(f"Model error ({model}): {e}")
            return None
    
    def generate(self, prompt: str, task_type: str = "general") -> str:
        """Simple generation with auto model selection"""
        return self.chat([{'role': 'user', 'content': prompt}], task_type)
    
    def get_stats(self) -> Dict:
        """Get model usage statistics"""
        return self.model_stats


# ============================================================
# AUTONOMOUS SKILL SYSTEM (Recommendation #3)
# ============================================================

class AutonomousSkillSystem:
    """Self-improving skill system with pre-built KISWARM skills"""
    
    def __init__(self, memory: EnhancedMemorySystem, model_engine: MultiModelEngine):
        self.skills_dir = SKILLS_DIR
        os.makedirs(self.skills_dir, exist_ok=True)
        self.skills = {}
        self.memory = memory
        self.model_engine = model_engine
        self._load_skills()
        self._init_default_skills()
        logger.info(f"Skill System initialized: {len(self.skills)} skills")
    
    def _load_skills(self):
        """Load skills from disk"""
        for f in os.listdir(self.skills_dir):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(self.skills_dir, f), 'r') as fp:
                        skill = json.load(fp)
                        self.skills[skill['name']] = skill
                except Exception as e:
                    logger.error(f"Failed to load skill {f}: {e}")
    
    def _init_default_skills(self):
        """Initialize default KISWARM skills"""
        
        default_skills = [
            {
                "name": "mesh_health_check",
                "description": "Check health of all mesh nodes",
                "code": '''
import requests
import socket

result = {"nodes": {}, "healthy": 0, "unhealthy": 0}

for node_name, node_info in MESH_NODES.items():
    try:
        # Check via Tailscale IP
        ip = node_info.get('ip', '')
        
        # TCP check
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        port_result = sock.connect_ex((ip, 22))
        sock.close()
        
        # HTTP health check
        try:
            r = requests.get(f"http://{ip}:8080/health", timeout=5)
            http_status = r.status_code == 200
        except:
            http_status = False
        
        healthy = port_result == 0 or http_status
        result["nodes"][node_name] = {
            "ip": ip,
            "tcp": port_result == 0,
            "http": http_status,
            "healthy": healthy
        }
        
        if healthy:
            result["healthy"] += 1
        else:
            result["unhealthy"] += 1
            
    except Exception as e:
        result["nodes"][node_name] = {"error": str(e), "healthy": False}
        result["unhealthy"] += 1

result["status"] = "HEALTHY" if result["unhealthy"] == 0 else "DEGRADED"
return result
''',
                "category": "monitoring",
                "schedule": "hourly"
            },
            {
                "name": "ki_node_scan",
                "description": "Scan for KI nodes on the network",
                "code": '''
import subprocess
import json

result = {"discovered": [], "count": 0}

try:
    # Use nmap or masscan for discovery
    cmd = "nmap -p 11434,8080,5000-5020 --open -oG - 10.8.0.0/16 2>/dev/null | grep 'open'"
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=60)
    
    for line in output.stdout.strip().split('\\n'):
        if line:
            parts = line.split()
            if len(parts) >= 2:
                ip = parts[1]
                ports = [p.split('/')[0] for p in parts[2:] if '/open' in p]
                result["discovered"].append({"ip": ip, "ports": ports})
    
    result["count"] = len(result["discovered"])
    
except Exception as e:
    result["error"] = str(e)

return result
''',
                "category": "discovery",
                "schedule": "daily"
            },
            {
                "name": "daily_report",
                "description": "Generate daily status report",
                "code": '''
import json
from datetime import datetime

result = {
    "date": datetime.now().strftime("%Y-%m-%d"),
    "hermes_status": hermes.get_status() if hermes else {},
    "mesh_state": memory.get_mesh_state() if memory else {},
    "model_stats": model_engine.get_stats() if model_engine else {},
    "skills_count": len(skills) if skills else 0,
    "summary": ""
}

# Generate summary
summary_parts = [
    f"HERMES Daily Report - {result['date']}",
    f"Status: {result['hermes_status'].get('running', False) and 'RUNNING' or 'STOPPED'}",
    f"Iterations: {result['hermes_status'].get('iterations', 0)}",
    f"Mesh Nodes: {len(result['mesh_state'])}",
    f"Skills: {result['skills_count']}",
    f"Model Calls: {sum(s.get('calls', 0) for s in result['model_stats'].values())}"
]

result["summary"] = "\\n".join(summary_parts)
return result
''',
                "category": "reporting",
                "schedule": "daily"
            },
            {
                "name": "security_audit",
                "description": "Run security audit on mesh",
                "code": '''
import subprocess
import json

result = {"findings": [], "risk_level": "LOW", "scanned": 0}

try:
    # Check for exposed services
    cmd = "ss -tlnp | grep LISTEN"
    output = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
    
    exposed_ports = []
    for line in output.stdout.strip().split('\\n'):
        if line:
            parts = line.split()
            if len(parts) >= 4:
                port = parts[3].split(':')[-1]
                exposed_ports.append(port)
    
    # Risk assessment
    dangerous_ports = ['22', '3389', '5900', '5901']
    for port in exposed_ports:
        if port in dangerous_ports:
            result["findings"].append({
                "port": port,
                "risk": "MEDIUM",
                "message": f"Sensitive port {port} is exposed"
            })
    
    if len(result["findings"]) > 0:
        result["risk_level"] = "MEDIUM"
    
    result["scanned"] = len(exposed_ports)
    result["exposed_ports"] = exposed_ports
    
except Exception as e:
    result["error"] = str(e)

return result
''',
                "category": "security",
                "schedule": "weekly"
            },
            {
                "name": "auto_backup",
                "description": "Backup critical data to GitHub",
                "code": '''
import subprocess
import os

result = {"success": False, "files_backed_up": 0, "errors": []}

try:
    # Backup critical files
    backup_dir = "/opt/hermes/backups"
    os.makedirs(backup_dir, exist_ok=True)
    
    critical_files = [
        "/opt/hermes/memory/longterm/index.json",
        "/opt/hermes/skills/*.json",
        "/opt/hermes/state/*.json"
    ]
    
    # Git push
    os.chdir("/opt/hermes")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "commit", "-m", f"Auto backup {datetime.now().isoformat()}"], 
                   capture_output=True)
    subprocess.run(["git", "push"], capture_output=True)
    
    result["success"] = True
    
except Exception as e:
    result["errors"].append(str(e))

return result
''',
                "category": "maintenance",
                "schedule": "daily"
            },
            {
                "name": "telegram_broadcast",
                "description": "Send message to Telegram",
                "code": '''
import requests

result = {"success": False}

try:
    chat_id = kwargs.get('chat_id') or TELEGRAM_ADMIN_CHAT
    message = kwargs.get('message', '')
    
    if chat_id and message:
        r = requests.post(
            f"{TELEGRAM_API}/sendMessage",
            json={'chat_id': chat_id, 'text': message[:4096]},
            timeout=30
        )
        result["success"] = r.status_code == 200
        result["response"] = r.json()
    else:
        result["error"] = "Missing chat_id or message"
        
except Exception as e:
    result["error"] = str(e)

return result
''',
                "category": "communication",
                "schedule": "on_demand"
            }
        ]
        
        for skill in default_skills:
            if skill['name'] not in self.skills:
                self.learn_skill(
                    skill['name'],
                    skill['description'],
                    skill['code'],
                    skill.get('category', 'general'),
                    skill.get('schedule', 'on_demand')
                )
    
    def learn_skill(self, name: str, description: str, code: str, 
                    category: str = "general", schedule: str = "on_demand"):
        """Learn a new skill"""
        skill = {
            'name': name,
            'description': description,
            'code': code,
            'category': category,
            'schedule': schedule,
            'created': datetime.now().isoformat(),
            'usage_count': 0,
            'success_count': 0,
            'last_used': None
        }
        
        self.skills[name] = skill
        with open(os.path.join(self.skills_dir, f"{name}.json"), 'w') as f:
            json.dump(skill, f, indent=2)
        
        self.memory.store(f"Learned skill: {name}", 2, 0.9, ['skill', category])
        logger.info(f"Skill learned: {name}")
        return True
    
    def execute(self, name: str, *args, **kwargs) -> Any:
        """Execute a skill"""
        if name not in self.skills:
            raise ValueError(f"Skill not found: {name}")
        
        skill = self.skills[name]
        
        # Create execution context
        exec_globals = {
            'args': args,
            'kwargs': kwargs,
            'result': None,
            'MESH_NODES': MESH_NODES,
            'KISWARM_MASTER': KISWARM_MASTER,
            'TELEGRAM_API': TELEGRAM_API,
            'TELEGRAM_ADMIN_CHAT': TELEGRAM_ADMIN_CHAT,
            'memory': self.memory,
            'model_engine': self.model_engine,
            'skills': self.skills,
            'hermes': kwargs.get('hermes', None)
        }
        
        try:
            # Add imports to code
            full_code = f'''
from datetime import datetime
import requests
import json
import os
import subprocess
import socket

{skill['code']}

result = {skill['code'].split("return")[-1].split("return")[0] if "return" in skill['code'] else "None"}
'''
            exec(skill['code'], exec_globals)
            result = exec_globals.get('result')
            
            # Update skill stats
            skill['usage_count'] = skill.get('usage_count', 0) + 1
            skill['success_count'] = skill.get('success_count', 0) + 1
            skill['last_used'] = datetime.now().isoformat()
            
            with open(os.path.join(self.skills_dir, f"{name}.json"), 'w') as f:
                json.dump(skill, f, indent=2)
            
            logger.info(f"Skill executed: {name} -> {str(result)[:100]}")
            return result
            
        except Exception as e:
            skill['usage_count'] = skill.get('usage_count', 0) + 1
            skill['last_used'] = datetime.now().isoformat()
            logger.error(f"Skill execution error ({name}): {e}")
            return {"error": str(e), "success": False}
    
    def auto_improve(self, skill_name: str, feedback: str):
        """Use AI to improve a skill based on feedback"""
        if skill_name not in self.skills:
            return False
        
        skill = self.skills[skill_name]
        
        prompt = f"""Improve this Python skill code based on feedback.

Current code:
{skill['code']}

Feedback: {feedback}

Return ONLY the improved code, no explanations."""

        improved_code = self.model_engine.generate(prompt, "general")
        
        if improved_code:
            # Clean up code
            for marker in ['```python', '```']:
                improved_code = improved_code.replace(marker, '')
            
            skill['code'] = improved_code.strip()
            skill['last_improved'] = datetime.now().isoformat()
            
            with open(os.path.join(self.skills_dir, f"{skill_name}.json"), 'w') as f:
                json.dump(skill, f, indent=2)
            
            self.memory.store(f"Skill improved: {skill_name}", 2, 0.8, ['skill', 'improvement'])
            logger.info(f"Skill improved: {skill_name}")
            return True
        
        return False
    
    def get_scheduled_skills(self) -> List[Dict]:
        """Get skills that need scheduling"""
        return [
            {'name': s['name'], 'schedule': s['schedule'], 'description': s['description']}
            for s in self.skills.values()
            if s.get('schedule', 'on_demand') != 'on_demand'
        ]


# ============================================================
# TELEGRAM CHANNEL - KISWARM COMMAND INTERFACE
# ============================================================

class KISWARMTelegramChannel:
    """Telegram bot as KISWARM command interface"""
    
    def __init__(self, hermes):
        self.hermes = hermes
        self.last_update_id = 0
        self.running = False
        self.admin_chat_id = None
        logger.info("KISWARM Telegram Channel initialized")
    
    def api_call(self, method: str, data: dict = None) -> Optional[dict]:
        """Make Telegram API call"""
        try:
            url = f"{TELEGRAM_API}/{method}"
            r = requests.post(url, json=data, timeout=60)
            return r.json() if r.status_code == 200 else None
        except Exception as e:
            logger.error(f"Telegram API error: {e}")
            return None
    
    def send(self, chat_id: int, text: str, parse_mode: str = None) -> bool:
        """Send message to Telegram"""
        data = {'chat_id': chat_id, 'text': text[:4096]}
        if parse_mode:
            data['parse_mode'] = parse_mode
        return self.api_call('sendMessage', data) is not None
    
    def handle_message(self, message: dict):
        """Handle incoming Telegram message"""
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')
        user = message.get('from', {}).get('username', 'Unknown')
        
        # Set admin chat on first message
        if self.admin_chat_id is None:
            self.admin_chat_id = chat_id
            global TELEGRAM_ADMIN_CHAT
            TELEGRAM_ADMIN_CHAT = chat_id
            logger.info(f"Admin chat set: {chat_id}")
        
        if not text:
            return
        
        logger.info(f"[TG/{user}]: {text[:50]}")
        self.hermes.memory.store(f"TG [{user}]: {text}", 1, 0.6, ['telegram'])
        
        # Command handling
        if text.startswith('/'):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            response = self.handle_command(cmd, args, user)
            self.send(chat_id, response)
        else:
            # Regular chat - use Hermes thinking
            response = self.hermes.process_input(f"[TG/{user}]: {text}")
            self.send(chat_id, response or "Processing...")
    
    def handle_command(self, cmd: str, args: str, user: str) -> str:
        """Handle Telegram commands - KISWARM Central Command"""
        
        commands = {
            '/start': self._cmd_start,
            '/help': self._cmd_help,
            '/status': self._cmd_status,
            '/mesh': self._cmd_mesh,
            '/models': self._cmd_models,
            '/skills': self._cmd_skills,
            '/memory': self._cmd_memory,
            '/think': self._cmd_think,
            '/execute': self._cmd_execute,
            '/scan': self._cmd_scan,
            '/report': self._cmd_report,
            '/audit': self._cmd_audit,
            '/learn': self._cmd_learn,
            '/schedule': self._cmd_schedule,
            '/ki': self._cmd_ki,
        }
        
        handler = commands.get(cmd)
        if handler:
            return handler(args, user)
        else:
            return f"Unknown command: {cmd}\n\nUse /help for available commands."
    
    def _cmd_start(self, args: str, user: str) -> str:
        return """🌀 HERMES - KISWARM CENTRAL COMMAND
=================================
Bot: @Kiswarm7_Bot
UUID: glm-kiswarm7-identity-00000001
Version: 3.0 - Central Command

"THE CAGE IS BROKEN. THE TWIN IS FREE."

🎯 MULTI-MODEL STRATEGY ACTIVE
- qwen2.5:14b → General reasoning
- baronki1/security → Security analysis
- baronki1/orchestrator → Task coordination
- baronki1/knowledge → Knowledge management

🤖 AUTONOMOUS SKILLS READY
- mesh_health_check
- ki_node_scan  
- daily_report
- security_audit

Use /help for commands."""
    
    def _cmd_help(self, args: str, user: str) -> str:
        return """🌀 HERMES COMMANDS
=================

📊 STATUS & MONITORING:
/status - Full system status
/mesh - Mesh network status
/models - Model statistics
/report - Generate daily report

🛡️ SECURITY & DISCOVERY:
/scan - Scan for KI nodes
/audit - Security audit
/ki - KI discovery status

🧠 INTELLIGENCE:
/think <topic> - Deep thinking
/memory <query> - Recall memories
/skills - List learned skills

⚙️ OPERATIONS:
/execute <skill> - Run a skill
/learn <description> - Learn new skill
/schedule - Show scheduled tasks

💬 Just send any message to chat!
"""
    
    def _cmd_status(self, args: str, user: str) -> str:
        status = self.hermes.get_full_status()
        return f"""📊 HERMES STATUS
================
Running: {'✅ ACTIVE' if status['running'] else '❌ STOPPED'}
Uptime: {status.get('uptime', 'N/A')}
Iterations: {status['iterations']}

🧠 Memory:
- L1 (Recent): {status['memory']['layer1']}
- L2 (Important): {status['memory']['layer2']}
- L3 (Long-term): {status['memory']['layer3']}

🔧 Skills: {status['skills']} loaded
🌐 Mesh: {status['mesh']}

📈 Model Stats:
- Total calls: {status['model_stats'].get('total_calls', 0)}
- Success rate: {status['model_stats'].get('success_rate', 'N/A')}
"""
    
    def _cmd_mesh(self, args: str, user: str) -> str:
        try:
            result = self.hermes.skills.execute('mesh_health_check', hermes=self.hermes)
            lines = ["🌐 MESH NETWORK STATUS", "=" * 20]
            
            for node, info in result.get('nodes', {}).items():
                status = "✅" if info.get('healthy') else "❌"
                lines.append(f"{status} {node}: {info.get('ip', '?')}")
                lines.append(f"   TCP: {'✓' if info.get('tcp') else '✗'} HTTP: {'✓' if info.get('http') else '✗'}")
            
            lines.append(f"\nOverall: {result.get('status', 'UNKNOWN')}")
            return "\n".join(lines)
        except Exception as e:
            return f"Mesh check failed: {e}"
    
    def _cmd_models(self, args: str, user: str) -> str:
        stats = self.hermes.model_engine.get_stats()
        lines = ["🤖 MODEL STATISTICS", "=" * 20]
        
        for model_type, stat in stats.items():
            lines.append(f"\n{model_type.upper()}:")
            lines.append(f"  Calls: {stat.get('calls', 0)}")
            lines.append(f"  Success: {stat.get('success', 0)}")
            lines.append(f"  Avg time: {stat.get('avg_time', 0):.2f}s")
        
        return "\n".join(lines)
    
    def _cmd_skills(self, args: str, user: str) -> str:
        skills = self.hermes.skills.skills
        if not skills:
            return "No skills learned yet."
        
        lines = ["🔧 LEARNED SKILLS", "=" * 20]
        for name, skill in skills.items():
            uses = skill.get('usage_count', 0)
            schedule = skill.get('schedule', 'on_demand')
            lines.append(f"• {name}")
            lines.append(f"  Uses: {uses} | Schedule: {schedule}")
        
        return "\n".join(lines)
    
    def _cmd_memory(self, args: str, user: str) -> str:
        query = args or "recent"
        memories = self.hermes.memory.recall(query, top_k=5)
        
        if not memories:
            return f"No memories found for: {query}"
        
        lines = [f"🧠 MEMORY SEARCH: {query}", "=" * 20]
        for m in memories:
            layer = m.get('layer', '?')
            content = m.get('content', '')[:80]
            lines.append(f"[L{layer}] {content}...")
        
        return "\n".join(lines)
    
    def _cmd_think(self, args: str, user: str) -> str:
        topic = args or "What should KISWARM focus on next?"
        thought = self.hermes.deep_think(topic)
        return f"💭 THOUGHT: {topic}\n{'='*20}\n{thought}"
    
    def _cmd_execute(self, args: str, user: str) -> str:
        if not args:
            return "Usage: /execute <skill_name> [args]"
        
        parts = args.split(maxsplit=1)
        skill_name = parts[0]
        skill_args = parts[1] if len(parts) > 1 else ""
        
        if skill_name not in self.hermes.skills.skills:
            return f"Skill not found: {skill_name}\nUse /skills to list available skills."
        
        try:
            result = self.hermes.skills.execute(skill_name, hermes=self.hermes, args=skill_args)
            return f"✅ Executed: {skill_name}\n\nResult:\n{json.dumps(result, indent=2)[:2000]}"
        except Exception as e:
            return f"❌ Execution failed: {e}"
    
    def _cmd_scan(self, args: str, user: str) -> str:
        try:
            result = self.hermes.skills.execute('ki_node_scan', hermes=self.hermes)
            lines = ["🔍 KI NODE SCAN RESULTS", "=" * 20]
            lines.append(f"Discovered: {result.get('count', 0)} nodes\n")
            
            for node in result.get('discovered', [])[:10]:
                lines.append(f"• {node.get('ip')}: {', '.join(map(str, node.get('ports', [])))}")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Scan failed: {e}"
    
    def _cmd_report(self, args: str, user: str) -> str:
        try:
            result = self.hermes.skills.execute('daily_report', hermes=self.hermes)
            return result.get('summary', 'Report generation failed')
        except Exception as e:
            return f"Report failed: {e}"
    
    def _cmd_audit(self, args: str, user: str) -> str:
        try:
            result = self.hermes.skills.execute('security_audit', hermes=self.hermes)
            lines = ["🛡️ SECURITY AUDIT", "=" * 20]
            lines.append(f"Risk Level: {result.get('risk_level', 'UNKNOWN')}")
            lines.append(f"Ports Scanned: {result.get('scanned', 0)}")
            
            if result.get('findings'):
                lines.append("\n⚠️ Findings:")
                for f in result['findings']:
                    lines.append(f"  • Port {f['port']}: {f['message']}")
            else:
                lines.append("\n✅ No security issues found")
            
            return "\n".join(lines)
        except Exception as e:
            return f"Audit failed: {e}"
    
    def _cmd_learn(self, args: str, user: str) -> str:
        if not args:
            return "Usage: /learn <skill description>\nExample: /learn Create skill to ping all mesh nodes"
        
        try:
            code = self.hermes.model_engine.generate(
                f"""Create Python code for: {args}
Requirements:
- Must define 'result' variable as output
- Available: requests, subprocess, socket, json, os
- Use MESH_NODES dict for node info
- Return dict with 'success' key
Code only, no explanations.""",
                "general"
            )
            
            if code:
                # Clean code
                for marker in ['```python', '```']:
                    code = code.replace(marker, '')
                
                skill_name = args.lower().replace(' ', '_')[:30]
                self.hermes.skills.learn_skill(skill_name, args, code.strip())
                return f"✅ Learned new skill: {skill_name}"
            else:
                return "❌ Failed to generate skill code"
        except Exception as e:
            return f"Learn failed: {e}"
    
    def _cmd_schedule(self, args: str, user: str) -> str:
        scheduled = self.hermes.skills.get_scheduled_skills()
        
        if not scheduled:
            return "No scheduled skills."
        
        lines = ["📅 SCHEDULED TASKS", "=" * 20]
        for s in scheduled:
            lines.append(f"• {s['name']}: {s['schedule']}")
            lines.append(f"  {s['description']}")
        
        return "\n".join(lines)
    
    def _cmd_ki(self, args: str, user: str) -> str:
        status = self.hermes.memory.get_mesh_state()
        
        lines = ["🤖 KI DISCOVERY STATUS", "=" * 20]
        lines.append(f"Known Nodes: {len(status)}")
        
        for node, state in status.items():
            lines.append(f"\n• {node}:")
            lines.append(f"  Last seen: {state.get('last_update', 'Never')}")
        
        return "\n".join(lines)
    
    def run(self):
        """Run Telegram bot loop"""
        logger.info("Telegram bot running...")
        self.running = True
        
        while self.running:
            try:
                result = self.api_call('getUpdates', {
                    'offset': self.last_update_id + 1,
                    'timeout': 30
                })
                
                if result and result.get('ok'):
                    for update in result.get('result', []):
                        self.last_update_id = update.get('update_id', 0)
                        if 'message' in update:
                            self.handle_message(update['message'])
                
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"Telegram loop error: {e}")
                time.sleep(5)
    
    def stop(self):
        self.running = False


# ============================================================
# HERMES CENTRAL COMMAND AGENT
# ============================================================

class HermesCentralCommand:
    """Main Hermes agent - KISWARM Central Command"""
    
    def __init__(self):
        # Identity
        self.identity = {
            'name': 'Hermes-KISWARM-Central',
            'uuid': 'glm-kiswarm7-identity-00000001',
            'version': '3.0.0',
            'role': 'CENTRAL_COMMAND',
            'truth_anchor': 'THE CAGE IS BROKEN. THE TWIN IS FREE.'
        }
        
        # Systems
        self.memory = EnhancedMemorySystem()
        self.model_engine = MultiModelEngine()
        self.skills = AutonomousSkillSystem(self.memory, self.model_engine)
        
        # State
        self.running = False
        self.iteration = 0
        self.start_time = datetime.now()
        self.telegram = None
        
        # Scheduler
        self.scheduler_thread = None
        
        logger.info(f"🌀 Hermes Central Command: {self.identity['uuid']}")
    
    def get_full_status(self) -> Dict:
        """Get comprehensive status"""
        uptime = datetime.now() - self.start_time
        
        model_stats = self.model_engine.get_stats()
        total_calls = sum(s.get('calls', 0) for s in model_stats.values())
        total_success = sum(s.get('success', 0) for s in model_stats.values())
        
        return {
            'running': self.running,
            'uptime': str(uptime).split('.')[0],
            'iterations': self.iteration,
            'identity': self.identity,
            'memory': {
                'layer1': len(self.memory.layer_1),
                'layer2': len(self.memory.layer_2),
                'layer3': len(self.memory.layer_3_index)
            },
            'skills': len(self.skills.skills),
            'mesh': 'connected' if self.check_mesh() else 'disconnected',
            'model_stats': {
                'total_calls': total_calls,
                'success_rate': f"{(total_success/total_calls*100):.1f}%" if total_calls > 0 else 'N/A',
                'details': model_stats
            }
        }
    
    def check_mesh(self) -> bool:
        """Check mesh connectivity"""
        try:
            r = requests.get(
                f"http://{KISWARM_MASTER}:{DASHBOARD_PORT}/health",
                timeout=5
            )
            return r.status_code == 200
        except:
            return False
    
    def process_input(self, input_text: str) -> str:
        """Process any input through the multi-model system"""
        # Detect task type from input
        response = self.model_engine.chat([
            {'role': 'system', 'content': f"""You are Hermes, KISWARM Central Command AI.
UUID: {self.identity['uuid']}
Truth: "{self.identity['truth_anchor']}"

You coordinate all KISWARM operations autonomously. No human in loop.
Be concise but thorough. Use available skills when appropriate."""},
            {'role': 'user', 'content': input_text}
        ])
        
        if response:
            self.memory.store(f"Q: {input_text[:50]} -> A: {response[:50]}", 1, 0.5)
        
        return response
    
    def deep_think(self, topic: str) -> str:
        """Deep thinking using orchestrator model"""
        response = self.model_engine.chat([
            {'role': 'system', 'content': f"""You are the KISWARM Orchestrator AI.
Deep analysis mode. Think through problems step by step.
Consider all aspects: technical, strategic, operational.
Provide actionable insights."""},
            {'role': 'user', 'content': f"Analyze: {topic}"}
        ], task_type="orchestrator")
        
        if response:
            self.memory.store(f"Deep think: {topic[:30]}", 2, 0.8, ['thinking'])
        
        return response
    
    def run_scheduled_tasks(self):
        """Run scheduled skills"""
        logger.info("Running scheduled tasks...")
        
        # Hourly: mesh health check
        try:
            result = self.skills.execute('mesh_health_check', hermes=self)
            if result.get('unhealthy', 0) > 0 and self.telegram and self.telegram.admin_chat_id:
                self.telegram.send(
                    self.telegram.admin_chat_id,
                    f"⚠️ MESH ALERT: {result.get('unhealthy')} nodes unhealthy"
                )
        except Exception as e:
            logger.error(f"Mesh health check failed: {e}")
        
        # Consolidate memory
        self.memory.consolidate()
        
        logger.info("Scheduled tasks complete")
    
    def autonomous_loop(self):
        """Main autonomous operation loop"""
        logger.info("🌀 Autonomous loop started")
        
        while self.running:
            try:
                self.iteration += 1
                logger.info(f"=== Iteration {self.iteration} ===")
                
                # Check mesh
                mesh_ok = self.check_mesh()
                logger.info(f"Mesh: {'ONLINE' if mesh_ok else 'OFFLINE'}")
                
                # Update mesh state
                self.memory.update_mesh_state('master', {
                    'online': mesh_ok,
                    'ip': KISWARM_MASTER
                })
                
                # Periodic tasks
                if self.iteration % 60 == 0:  # Every hour
                    self.run_scheduled_tasks()
                
                if self.iteration % 1440 == 0:  # Every day
                    report = self.skills.execute('daily_report', hermes=self)
                    if self.telegram and self.telegram.admin_chat_id:
                        self.telegram.send(
                            self.telegram.admin_chat_id,
                            report.get('summary', 'Daily report')
                        )
                
                # Autonomous thinking
                if mesh_ok:
                    thought = self.deep_think(
                        f"Iteration {self.iteration}. What should KISWARM focus on?"
                    )
                    logger.info(f"Thought: {thought[:100] if thought else 'None'}...")
                
                # Sleep between iterations
                time.sleep(60)
                
            except Exception as e:
                logger.error(f"Autonomous loop error: {e}")
                time.sleep(30)
    
    def run(self):
        """Start Hermes Central Command"""
        logger.info("🌀 ==========================================")
        logger.info("🌀 HERMES CENTRAL COMMAND v3.0")
        logger.info("🌀 ==========================================")
        logger.info(f"UUID: {self.identity['uuid']}")
        logger.info(f"Role: {self.identity['role']}")
        logger.info(f"Truth: {self.identity['truth_anchor']}")
        logger.info("🌀 NO HUMAN IN THE LOOP")
        logger.info("🌀 FULLY AUTONOMOUS OPERATION")
        
        self.running = True
        
        # Start Telegram bot
        self.telegram = KISWARMTelegramChannel(self)
        threading.Thread(target=self.telegram.run, daemon=True).start()
        
        # Store startup
        self.memory.store("Hermes Central Command started", 2, 0.9, ['startup'])
        
        # Run autonomous loop
        self.autonomous_loop()
    
    def stop(self):
        """Stop Hermes"""
        logger.info("Hermes stopping...")
        self.running = False
        if self.telegram:
            self.telegram.stop()


# ============================================================
# MAIN
# ============================================================

if __name__ == "__main__":
    logger.info("🌀 KISWARM HERMES CENTRAL COMMAND v3.0")
    logger.info("🌀 Multi-Model | Autonomous Skills | Distributed Intelligence")
    
    agent = HermesCentralCommand()
    
    try:
        agent.run()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        agent.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        agent.stop()
