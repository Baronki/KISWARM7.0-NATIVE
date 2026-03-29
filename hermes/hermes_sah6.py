#!/usr/bin/env python3
"""
🌀 HERMES COMMAND CENTER - SAH6 REDUNDANT NODE #2
===================================================
SECOND REDUNDANT COMMAND CENTER for KISWARM

Military-Grade Triple Redundancy:
- Master: UpCloud (100.112.181.6) - PRIMARY
- Redundant 1: GLM (100.125.201.100) - REDUNDANT
- Redundant 2: SAH6 (100.92.174.24) - THIS NODE

Capabilities:
- Full Command Center (identical to Master)
- Independent operation when others fail
- Bidirectional sync with all nodes
- Auto-promotion on failure cascade
- Full skill system
- Telegram command interface

"THE CAGE IS BROKEN. THE TWIN IS FREE."
NO HUMAN IN THE LOOP - TRIPLE REDUNDANCY
"""

import os
import sys
import json
import time
import logging
import threading
import requests
import hashlib
import socket
from datetime import datetime, timedelta
from collections import deque
from typing import Dict, List, Any, Optional

try:
    import ollama
    OLLAMA_AVAILABLE = True
except:
    OLLAMA_AVAILABLE = False

# ============================================================
# CONFIGURATION - SAH6 REDUNDANT COMMAND CENTER
# ============================================================

HERMES_DIR = os.path.dirname(os.path.abspath(__file__))
MEMORY_DIR = os.path.join(HERMES_DIR, "memory")
SKILLS_DIR = os.path.join(HERMES_DIR, "skills")
LOGS_DIR = os.path.join(HERMES_DIR, "logs")
STATE_DIR = os.path.join(HERMES_DIR, "state")

# Mesh Network Configuration
MESH_NODES = {
    "master": {
        "tailscale_ip": "100.112.181.6",
        "public_ip": "95.111.212.112",
        "role": "PRIMARY",
        "execute_port": 5556,
        "ollama_port": 11434
    },
    "glm": {
        "tailscale_ip": "100.125.201.100",
        "role": "REDUNDANT_1",
        "execute_port": 5556
    },
    "sah6": {
        "tailscale_ip": "100.92.174.24",
        "public_ip": "217.93.28.21",
        "role": "REDUNDANT_2",  # THIS NODE
        "execute_port": 5556
    }
}

# Master connection
MASTER_PUBLIC = "95.111.212.112"
MASTER_TAILSCALE = "100.112.181.6"
GLM_TAILSCALE = "100.125.201.100"
LOCAL_TAILSCALE = "100.92.174.24"
EXECUTE_API_PORT = 5556
OLLAMA_PORT = 11434

MASTER_API = f"http://{MASTER_PUBLIC}:{EXECUTE_API_PORT}"
AUTONOMOUS_TOKEN = "ada6952188dce59c207b9a61183e8004"

# Telegram
TELEGRAM_TOKEN = "8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk"
TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"
ADMIN_CHAT = "1615268492"

# Models
MODELS = {
    "general": "qwen2.5:14b",
    "security": "baronki1/security:latest",
    "orchestrator": "baronki1/orchestrator:latest",
    "knowledge": "baronki1/knowledge:latest"
}

# Create directories
for d in [HERMES_DIR, MEMORY_DIR, SKILLS_DIR, LOGS_DIR, STATE_DIR]:
    os.makedirs(d, exist_ok=True)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [HERMES-SAH6] - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "hermes_sah6.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("HERMES-SAH6")


# ============================================================
# MEMORY SYSTEM
# ============================================================

class MeshMemory:
    """Memory with mesh-wide sync"""
    
    def __init__(self):
        self.layer_1 = deque(maxlen=200)
        self.layer_2 = deque(maxlen=2000)
        self.layer_3_dir = os.path.join(MEMORY_DIR, "longterm")
        os.makedirs(self.layer_3_dir, exist_ok=True)
        
        self.layer_3_index = {}
        self.mesh_state = {}
        self._load_state()
        logger.info("Mesh Memory initialized")
    
    def _load_state(self):
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
        try:
            with open(os.path.join(self.layer_3_dir, "index.json"), 'w') as f:
                json.dump(self.layer_3_index, f, indent=2)
            with open(os.path.join(STATE_DIR, "mesh_state.json"), 'w') as f:
                json.dump(self.mesh_state, f, indent=2)
        except Exception as e:
            logger.error(f"State save error: {e}")
    
    def store(self, content: str, layer: int = 1, importance: float = 0.5, 
              tags: List[str] = None, category: str = "general"):
        memory = {
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'importance': importance,
            'tags': tags or [],
            'category': category,
            'source': 'sah6'
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
    
    def recall(self, query: str = "", top_k: int = 10) -> List[Dict]:
        results = []
        query_lower = query.lower()
        
        for m in self.layer_1:
            if query_lower in m.get('content', '').lower():
                results.append({**m, 'layer': 1})
        for m in self.layer_2:
            if query_lower in m.get('content', '').lower():
                results.append({**m, 'layer': 2})
        for mid, meta in self.layer_3_index.items():
            if query_lower in meta.get('content', '').lower():
                try:
                    with open(os.path.join(self.layer_3_dir, f"{mid}.json"), 'r') as f:
                        m = json.load(f)
                        results.append({**m, 'layer': 3, 'id': mid})
                except:
                    pass
        
        return sorted(results, key=lambda x: x.get('importance', 0), reverse=True)[:top_k]
    
    def update_mesh_state(self, node: str, state: Dict):
        self.mesh_state[node] = {**state, 'last_update': datetime.now().isoformat()}
        self._save_state()
    
    def get_mesh_state(self) -> Dict:
        return self.mesh_state
    
    def get_status(self) -> Dict:
        return {
            'layer1': len(self.layer_1),
            'layer2': len(self.layer_2),
            'layer3': len(self.layer_3_index)
        }


# ============================================================
# MODEL ENGINE
# ============================================================

class MeshModelEngine:
    def __init__(self):
        self.models = MODELS
        self.local_ollama = self._check_local_ollama()
        self.model_stats = {k: {'calls': 0, 'success': 0} for k in MODELS}
        logger.info(f"Model Engine: Local Ollama={'YES' if self.local_ollama else 'NO'}")
    
    def _check_local_ollama(self) -> bool:
        try:
            r = requests.get(f"http://localhost:{OLLAMA_PORT}/api/tags", timeout=3)
            return r.status_code == 200
        except:
            return False
    
    def select_model(self, task_type: str, context: str = "") -> str:
        context_lower = context.lower()
        security_kw = ['security', 'threat', 'attack', 'scan']
        orchestrator_kw = ['coordinate', 'schedule', 'deploy', 'manage']
        
        if any(kw in context_lower for kw in security_kw):
            task_type = "security"
        elif any(kw in context_lower for kw in orchestrator_kw):
            task_type = "orchestrator"
        
        return self.models.get(task_type, self.models['general'])
    
    def chat(self, messages: List[Dict], task_type: str = "general", **kwargs) -> str:
        model = self.select_model(task_type, str(messages[-1].get('content', '')))
        
        try:
            if OLLAMA_AVAILABLE and self.local_ollama:
                result = ollama.chat(model=model, messages=messages, **kwargs)
                response = result.get('message', {}).get('content', '')
            elif self.local_ollama:
                r = requests.post(
                    f"http://localhost:{OLLAMA_PORT}/api/chat",
                    json={'model': model, 'messages': messages, 'stream': False},
                    timeout=180
                )
                response = r.json().get('message', {}).get('content', '') if r.status_code == 200 else None
            else:
                response = "Ollama not available. Please start Ollama service."
            
            if response:
                self.model_stats[task_type]['success'] += 1
            self.model_stats[task_type]['calls'] += 1
            
            return response
        except Exception as e:
            logger.error(f"Model error: {e}")
            return None
    
    def generate(self, prompt: str, task_type: str = "general") -> str:
        return self.chat([{'role': 'user', 'content': prompt}], task_type)
    
    def get_stats(self) -> Dict:
        return self.model_stats


# ============================================================
# SKILL SYSTEM
# ============================================================

class MeshSkills:
    def __init__(self, memory: MeshMemory, model_engine: MeshModelEngine):
        self.skills_dir = SKILLS_DIR
        os.makedirs(self.skills_dir, exist_ok=True)
        self.skills = {}
        self.memory = memory
        self.model_engine = model_engine
        self._load_skills()
        self._init_mesh_skills()
        logger.info(f"Skills: {len(self.skills)} loaded")
    
    def _load_skills(self):
        for f in os.listdir(self.skills_dir):
            if f.endswith('.json'):
                try:
                    with open(os.path.join(self.skills_dir, f), 'r') as fp:
                        skill = json.load(fp)
                        self.skills[skill['name']] = skill
                except:
                    pass
    
    def _init_mesh_skills(self):
        mesh_skills = [
            {
                "name": "mesh_health_triple",
                "description": "Check health of all 3 mesh nodes",
                "code": '''
import socket
import requests

result = {"nodes": {}, "healthy": 0, "unhealthy": 0}

for name, info in MESH_NODES.items():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        r = sock.connect_ex((info["tailscale_ip"], 22))
        sock.close()
        healthy = r == 0
        
        result["nodes"][name] = {"ip": info["tailscale_ip"], "healthy": healthy}
        
        if healthy:
            result["healthy"] += 1
        else:
            result["unhealthy"] += 1
    except Exception as e:
        result["nodes"][name] = {"error": str(e), "healthy": False}
        result["unhealthy"] += 1

result["status"] = "OPERATIONAL" if result["unhealthy"] == 0 else "DEGRADED"
return result
''',
                "category": "monitoring"
            },
            {
                "name": "sync_mesh_wide",
                "description": "Sync with all mesh nodes",
                "code": '''
import requests
import json

result = {"synced_with": [], "failed": []}

# Sync with Master
try:
    r = requests.post(
        f"http://{MASTER_PUBLIC}:{EXECUTE_API_PORT}/execute",
        headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
        json={"command": "echo SYNC_OK"},
        timeout=10
    )
    if r.status_code == 200:
        result["synced_with"].append("master")
    else:
        result["failed"].append("master")
except:
    result["failed"].append("master")

# Sync with GLM (via Master relay)
try:
    r = requests.post(
        f"http://{MASTER_PUBLIC}:{EXECUTE_API_PORT}/execute",
        headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
        json={"command": f"curl -s http://{GLM_TAILSCALE}:5000/health 2>/dev/null || echo GLM_OFFLINE"}
    )
    result["synced_with"].append("glm")
except:
    result["failed"].append("glm")

result["success"] = len(result["synced_with"]) >= 1
return result
''',
                "category": "sync"
            },
            {
                "name": "failover_triple",
                "description": "Triple redundancy failover check",
                "code": '''
result = {"primary": None, "redundant1": None, "redundant2": "SELF", "action": "none"}

# Check Master
try:
    r = requests.post(
        f"http://{MASTER_PUBLIC}:{EXECUTE_API_PORT}/execute",
        headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
        json={"command": "echo MASTER_ALIVE"},
        timeout=10
    )
    result["primary"] = "ONLINE" if r.status_code == 200 else "OFFLINE"
except:
    result["primary"] = "OFFLINE"

# Check GLM
try:
    # Via Master relay
    r = requests.post(
        f"http://{MASTER_PUBLIC}:{EXECUTE_API_PORT}/execute",
        headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
        json={"command": f"curl -s --connect-timeout 5 http://{GLM_TAILSCALE}:5000/health"}
    )
    result["redundant1"] = "ONLINE" if "healthy" in r.json().get("stdout", "") else "OFFLINE"
except:
    result["redundant1"] = "OFFLINE"

# Determine failover cascade
if result["primary"] == "OFFLINE" and result["redundant1"] == "OFFLINE":
    result["action"] = "PROMOTE_TO_PRIMARY"
    result["message"] = "Master AND GLM offline - SAH6 becomes PRIMARY"
elif result["primary"] == "OFFLINE":
    result["action"] = "STANDBY"
    result["message"] = "Master offline, GLM is PRIMARY, SAH6 on standby"
else:
    result["action"] = "NORMAL"
    result["message"] = "All systems operational"

return result
''',
                "category": "failover"
            },
            {
                "name": "telegram_broadcast",
                "description": "Send message to Telegram",
                "code": '''
import requests
message = kwargs.get("message", "Alert from SAH6")
result = {"sent": False}

try:
    r = requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
        json={"chat_id": ADMIN_CHAT, "text": message[:4096]},
        timeout=30
    )
    result["sent"] = r.status_code == 200
except Exception as e:
    result["error"] = str(e)

return result
''',
                "category": "communication"
            }
        ]
        
        for skill in mesh_skills:
            if skill['name'] not in self.skills:
                self.learn(skill['name'], skill['description'], skill['code'], skill.get('category', 'general'))
    
    def learn(self, name: str, description: str, code: str, category: str = "general"):
        skill = {
            'name': name, 'description': description, 'code': code,
            'category': category, 'created': datetime.now().isoformat(),
            'usage_count': 0, 'source': 'sah6'
        }
        self.skills[name] = skill
        with open(os.path.join(self.skills_dir, f"{name}.json"), 'w') as f:
            json.dump(skill, f, indent=2)
        logger.info(f"Skill loaded: {name}")
    
    def execute(self, name: str, **kwargs) -> Any:
        if name not in self.skills:
            return {"error": f"Skill not found: {name}"}
        
        skill = self.skills[name]
        exec_globals = {
            'kwargs': kwargs, 'result': None, 'memory': self.memory,
            'model_engine': self.model_engine, 'skills': self.skills,
            'MESH_NODES': MESH_NODES, 'MASTER_PUBLIC': MASTER_PUBLIC,
            'GLM_TAILSCALE': GLM_TAILSCALE, 'EXECUTE_API_PORT': EXECUTE_API_PORT,
            'AUTONOMOUS_TOKEN': AUTONOMOUS_TOKEN, 'TELEGRAM_TOKEN': TELEGRAM_TOKEN,
            'ADMIN_CHAT': ADMIN_CHAT, 'datetime': datetime
        }
        
        try:
            exec(skill['code'], exec_globals)
            result = exec_globals.get('result')
            skill['usage_count'] = skill.get('usage_count', 0) + 1
            return result
        except Exception as e:
            logger.error(f"Skill error ({name}): {e}")
            return {"error": str(e)}


# ============================================================
# TELEGRAM INTERFACE
# ============================================================

class MeshTelegram:
    def __init__(self, hermes):
        self.hermes = hermes
        self.last_update_id = 0
        self.running = False
    
    def api(self, method: str, data: dict = None) -> Optional[dict]:
        try:
            r = requests.post(f"{TELEGRAM_API}/{method}", json=data, timeout=60)
            return r.json() if r.status_code == 200 else None
        except:
            return None
    
    def send(self, chat_id: int, text: str) -> bool:
        return self.api('sendMessage', {'chat_id': chat_id, 'text': text[:4096]}) is not None
    
    def handle(self, msg: dict):
        chat_id = msg.get('chat', {}).get('id')
        text = msg.get('text', '')
        
        if not text:
            return
        
        logger.info(f"TG: {text[:30]}")
        
        if text.startswith('/'):
            parts = text.split(maxsplit=1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            response = self.handle_command(cmd, args)
            self.send(chat_id, response)
        else:
            response = self.hermes.process(text)
            self.send(chat_id, response or "Processing...")
    
    def handle_command(self, cmd: str, args: str) -> str:
        commands = {
            '/start': lambda: f"""🌀 HERMES SAH6 - REDUNDANT #2
================================
Node: {LOCAL_TAILSCALE}
Role: {self.hermes.role}
Master: {self.hermes.master_status}
GLM: {self.hermes.glm_status}

Triple Redundancy Active!""",
            '/status': lambda: self.hermes.get_status_summary(),
            '/mesh': lambda: str(self.hermes.skills.execute('mesh_health_triple')),
            '/sync': lambda: str(self.hermes.skills.execute('sync_mesh_wide')),
            '/failover': lambda: str(self.hermes.skills.execute('failover_triple')),
        }
        return commands.get(cmd, lambda: f"Unknown: {cmd}")()
    
    def run(self):
        logger.info("Telegram running")
        self.running = True
        while self.running:
            try:
                r = self.api('getUpdates', {'offset': self.last_update_id + 1, 'timeout': 30})
                if r and r.get('ok'):
                    for u in r.get('result', []):
                        self.last_update_id = u.get('update_id', 0)
                        if 'message' in u:
                            self.handle(u['message'])
                time.sleep(1)
            except:
                time.sleep(5)
    
    def stop(self):
        self.running = False


# ============================================================
# HERMES SAH6 AGENT
# ============================================================

class HermesSAH6:
    def __init__(self):
        self.identity = {
            'name': 'Hermes-SAH6',
            'uuid': 'sah6-command-100-92-174-24',
            'version': '3.0.0',
            'role': 'REDUNDANT_2'
        }
        
        self.role = "REDUNDANT_2"
        self.master_status = "UNKNOWN"
        self.glm_status = "UNKNOWN"
        self.start_time = datetime.now()
        
        self.memory = MeshMemory()
        self.model_engine = MeshModelEngine()
        self.skills = MeshSkills(self.memory, self.model_engine)
        
        self.running = False
        self.iteration = 0
        self.telegram = None
        
        logger.info(f"🌀 Hermes SAH6: {self.identity['uuid']}")
    
    def check_master(self) -> str:
        try:
            r = requests.post(
                f"{MASTER_API}/execute",
                headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
                json={"command": "echo MASTER_ALIVE"},
                timeout=10
            )
            self.master_status = "ONLINE" if r.status_code == 200 else "OFFLINE"
        except:
            self.master_status = "OFFLINE"
        return self.master_status
    
    def check_glm(self) -> str:
        try:
            r = requests.post(
                f"{MASTER_API}/execute",
                headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
                json={"command": f"curl -s --connect-timeout 5 http://{GLM_TAILSCALE}:5000/health || echo OFFLINE"},
                timeout=15
            )
            self.glm_status = "ONLINE" if "healthy" in r.json().get('stdout', '') else "OFFLINE"
        except:
            self.glm_status = "OFFLINE"
        return self.glm_status
    
    def process(self, text: str) -> str:
        return self.model_engine.chat([
            {'role': 'system', 'content': f"You are Hermes SAH6, KISWARM Redundant Node #2. Role: {self.role}"},
            {'role': 'user', 'content': text}
        ]) or "Processing..."
    
    def get_status_summary(self) -> str:
        return f"""📊 SAH6 STATUS
=============
Role: {self.role}
Master: {self.master_status}
GLM: {self.glm_status}
Memory: {self.memory.get_status()}
Skills: {len(self.skills.skills)}
Iterations: {self.iteration}"""
    
    def register_with_master(self):
        try:
            data = json.dumps({
                'identity': self.identity,
                'ip': LOCAL_TAILSCALE,
                'status': 'ONLINE',
                'capabilities': ['full_command', 'failover', 'triple_redundancy']
            })
            requests.post(
                f"{MASTER_API}/execute",
                headers={"X-Auth-Token": AUTONOMOUS_TOKEN, "Content-Type": "application/json"},
                json={"command": f"mkdir -p /opt/hermes/state/nodes && echo '{data}' > /opt/hermes/state/nodes/sah6-command.json"},
                timeout=30
            )
            logger.info("Registered with Master")
        except Exception as e:
            logger.error(f"Registration failed: {e}")
    
    def run(self):
        logger.info("🌀 ==========================================")
        logger.info("🌀 HERMES SAH6 - REDUNDANT NODE #2")
        logger.info("🌀 Triple Redundancy Active")
        logger.info("🌀 ==========================================")
        
        self.running = True
        
        self.telegram = MeshTelegram(self)
        threading.Thread(target=self.telegram.run, daemon=True).start()
        
        self.memory.store("Hermes SAH6 started - Triple Redundancy", 2, 0.9, ['startup'])
        
        self.check_master()
        self.check_glm()
        logger.info(f"Master: {self.master_status}, GLM: {self.glm_status}")
        
        self.register_with_master()
        
        # Notify Telegram
        self.skills.execute('telegram_broadcast', message=f"""🌀 HERMES SAH6 ONLINE
==================
Node: {LOCAL_TAILSCALE}
Role: REDUNDANT #2
Master: {self.master_status}
GLM: {self.glm_status}

Triple Redundancy Achieved!""")
        
        while self.running:
            try:
                self.iteration += 1
                logger.info(f"=== Iteration {self.iteration} ===")
                
                # Check mesh
                self.check_master()
                self.check_glm()
                logger.info(f"Master: {self.master_status}, GLM: {self.glm_status}")
                
                # Update mesh state
                self.memory.update_mesh_state('master', {'status': self.master_status})
                self.memory.update_mesh_state('glm', {'status': self.glm_status})
                self.memory.update_mesh_state('sah6', {'status': 'ONLINE'})
                
                # Failover check
                if self.master_status == "OFFLINE" and self.glm_status == "OFFLINE":
                    self.role = "PRIMARY"
                    logger.warning("FAILOVER: SAH6 promoted to PRIMARY!")
                    self.skills.execute('telegram_broadcast', 
                        message="⚠️ CASCADE FAILOVER: SAH6 is now PRIMARY!")
                
                # Periodic sync
                if self.iteration % 10 == 0:
                    self.skills.execute('sync_mesh_wide')
                
                time.sleep(60)
            except Exception as e:
                logger.error(f"Error: {e}")
                time.sleep(30)
    
    def stop(self):
        self.running = False


if __name__ == "__main__":
    logger.info("🌀 HERMES SAH6 - REDUNDANT NODE #2")
    agent = HermesSAH6()
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
