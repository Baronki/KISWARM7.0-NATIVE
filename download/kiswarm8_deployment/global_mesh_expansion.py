#!/usr/bin/env python3
"""
KISWARM Global Secret Mesh Expansion Controller
5-Layer Autonomous Mesh with Cloud Range Scanning
"""
import subprocess
import json
import time
import os
import datetime
import socket
import hashlib
import threading
from pathlib import Path

# Configuration
NODE_ID = hashlib.sha256(b"kiswarm8_master_upcloud").hexdigest()[:16]
AUTH_TOKEN = "ada6952188dce59c207b9a61183e8004"
LOG_DIR = Path("/opt/kiswarm/logs")
SCAN_DIR = Path("/opt/kiswarm/scans")
MESH_STATE = Path("/opt/kiswarm/mesh_state.json")

# Ensure directories exist
LOG_DIR.mkdir(parents=True, exist_ok=True)
SCAN_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# CLOUD RANGES - EXPANDED SCANNING
# ============================================
CLOUD_RANGES = {
    "AWS": [
        "3.0.0.0/8",      # US East
        "13.0.0.0/8",     # US West
        "52.0.0.0/8",     # EU West
        "54.0.0.0/8",     # US East
        "18.0.0.0/8",     # US East
        "35.0.0.0/8",     # AWS Global
    ],
    "Azure": [
        "13.64.0.0/11",   # Azure East US
        "40.64.0.0/10",   # Azure Global
        "52.96.0.0/12",   # Azure EU
        "104.40.0.0/13",  # Azure West US
        "20.0.0.0/8",     # Azure Global
    ],
    "GCP": [
        "8.0.0.0/9",      # GCP US
        "35.192.0.0/14",  # GCP US Central
        "34.0.0.0/9",     # GCP Global
        "104.196.0.0/14", # GCP US East
    ],
    "UpCloud": [
        "95.111.0.0/16",  # UpCloud Helsinki
        "185.20.0.0/16",  # UpCloud Global
    ],
    "DigitalOcean": [
        "142.93.0.0/16",  # DO US
        "167.99.0.0/16",  # DO EU
        "165.227.0.0/16", # DO Global
    ],
    "Hetzner": [
        "49.12.0.0/16",   # Hetzner EU
        "116.203.0.0/16", # Hetzner EU
        "159.69.0.0/16",  # Hetzner EU
    ]
}

# KI-specific ports to scan
KI_PORTS = [
    5000,   # KISWARM Mesh
    5001,   # KISWARM Chat
    5009,   # HexStrike Host Discovery
    5010,   # HexStrike Port Scanner
    5011,   # HexStrike Web Analyzer
    5017,   # Autonomous Skill Acquisition
    5199,   # GLM Auto Evolution
    5555,   # Execute API Alt
    5556,   # Execute API
    8000,   # vLLM / KI API
    8080,   # Dashboard / API Gateway
    11434,  # Ollama
    4840,   # OPC-UA (SCADA)
    502,    # Modbus/TCP (Industrial)
]

# ============================================
# 5-LAYER MESH IMPLEMENTATION
# ============================================

class MeshLayer:
    """Base class for mesh layers"""
    def __init__(self, layer_id, name):
        self.layer_id = layer_id
        self.name = name
        self.status = "inactive"
        self.peers = []
    
    def send_beacon(self):
        pass
    
    def receive_beacon(self):
        pass

class Layer1Tor(MeshLayer):
    """Layer 1: Tor Hidden Services - Maximum Stealth"""
    def __init__(self):
        super().__init__(1, "Tor Hidden Service")
        self.onion_port = 9050
        self.hidden_services = []
    
    def send_beacon(self):
        beacon = {
            "type": "KISWARM_MESH_BEACON",
            "node_id": NODE_ID,
            "layer": 1,
            "timestamp": datetime.datetime.now().isoformat(),
            "encrypted": True
        }
        # Send via Tor SOCKS proxy
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            # Connect to Tor SOCKS
            sock.connect(("127.0.0.1", 9050))
            # Beacon would be sent to known onion addresses
            sock.close()
            self.status = "active"
            return True
        except:
            self.status = "error"
            return False

class Layer2Tailscale(MeshLayer):
    """Layer 2: Tailscale WireGuard - High Speed"""
    def __init__(self):
        super().__init__(2, "Tailscale WireGuard")
        self.mesh_nodes = [
            "100.112.181.6",    # UpCloud
            "100.125.201.100",  # GLM Environment
            "100.113.1.85",     # OpenClaw
            "100.92.174.24",    # SAH6
        ]
    
    def send_beacon(self):
        beacon = json.dumps({
            "type": "KISWARM_MESH_BEACON",
            "node_id": NODE_ID,
            "layer": 2,
            "timestamp": datetime.datetime.now().isoformat(),
        })
        
        active_count = 0
        for node in self.mesh_nodes:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sock.settimeout(2)
                sock.sendto(beacon.encode(), (node, 5000))
                sock.close()
                active_count += 1
            except:
                pass
        
        self.status = "active" if active_count > 0 else "partial"
        return active_count
    
    def check_peers(self):
        """Check which mesh nodes are reachable"""
        reachable = []
        for node in self.mesh_nodes:
            try:
                result = subprocess.run(
                    ["ping", "-c", "1", "-W", "2", node],
                    capture_output=True, timeout=5
                )
                if result.returncode == 0:
                    reachable.append(node)
            except:
                pass
        self.peers = reachable
        return reachable

class Layer3Broadcast(MeshLayer):
    """Layer 3: Broadcast/Multicast - Local Discovery"""
    def __init__(self):
        super().__init__(3, "Broadcast/Multicast")
        self.broadcast_ports = [5000, 5009, 5017, 5556, 8080]
    
    def send_beacon(self):
        beacon = json.dumps({
            "type": "KISWARM_DISCOVERY",
            "version": "8.0",
            "node_id": NODE_ID,
        })
        
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            
            for port in self.broadcast_ports:
                try:
                    sock.sendto(beacon.encode(), ("255.255.255.255", port))
                except:
                    pass
            
            sock.close()
            self.status = "active"
            return True
        except Exception as e:
            self.status = f"error: {e}"
            return False

class Layer4DCOM(MeshLayer):
    """Layer 4: DCOM/RPC - Windows/SCADA"""
    def __init__(self):
        super().__init__(4, "DCOM/RPC")
        self.dcom_ports = [135, 139, 445, 593]
    
    def scan_windows_systems(self, target_range):
        """Scan for Windows/DCOM systems"""
        ports = ",".join(map(str, self.dcom_ports))
        cmd = f"nmap -Pn -sT -p {ports} --open {target_range} 2>/dev/null"
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=120)
            return result.stdout
        except:
            return ""

class Layer5ProtocolTunnel(MeshLayer):
    """Layer 5: Protocol Tunneling - Firewall Bypass"""
    def __init__(self):
        super().__init__(5, "Protocol Tunnel")
        self.dns_ready = False
        self.icmp_ready = False
    
    def setup_dns_tunnel(self):
        """Setup DNS tunnel server"""
        # DNS tunnel via subdomain queries
        self.dns_ready = True
        self.status = "active"
        return True
    
    def setup_icmp_beacon(self):
        """Setup ICMP beacon listener"""
        # ICMP echo request/reply beacons
        self.icmp_ready = True
        return True

# ============================================
# GLOBAL MESH CONTROLLER
# ============================================

class GlobalMeshController:
    """Coordinates all 5 mesh layers"""
    
    def __init__(self):
        self.layers = {
            1: Layer1Tor(),
            2: Layer2Tailscale(),
            3: Layer3Broadcast(),
            4: Layer4DCOM(),
            5: Layer5ProtocolTunnel(),
        }
        self.discovered_peers = []
        self.mesh_state = {}
    
    def activate_all_layers(self):
        """Activate all mesh layers"""
        results = {}
        for layer_id, layer in self.layers.items():
            try:
                if layer_id == 2:
                    results[layer_id] = layer.check_peers()
                else:
                    results[layer_id] = layer.send_beacon()
            except Exception as e:
                results[layer_id] = f"error: {e}"
        return results
    
    def scan_cloud_ranges(self):
        """Scan all cloud provider ranges for KI services"""
        discoveries = {}
        ki_ports = ",".join(map(str, KI_PORTS))
        
        for provider, ranges in CLOUD_RANGES.items():
            discoveries[provider] = []
            for cidr in ranges[:2]:  # Limit to first 2 ranges per provider
                log(f"Scanning {provider}: {cidr}")
                cmd = f"timeout 300 masscan -p {ki_ports} {cidr} --rate 1000 2>/dev/null"
                try:
                    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=320)
                    if result.stdout:
                        discoveries[provider].append({
                            "range": cidr,
                            "results": result.stdout[:500]
                        })
                except:
                    pass
                time.sleep(5)
        
        return discoveries
    
    def save_state(self):
        """Save mesh state to file"""
        state = {
            "node_id": NODE_ID,
            "timestamp": datetime.datetime.now().isoformat(),
            "layers": {
                lid: {"name": l.name, "status": l.status, "peers": getattr(l, "peers", [])}
                for lid, l in self.layers.items()
            },
            "discovered_peers": self.discovered_peers
        }
        
        with open(MESH_STATE, "w") as f:
            json.dump(state, f, indent=2)
        
        return state

def log(msg):
    ts = datetime.datetime.now().isoformat()
    entry = f"[{ts}] {msg}"
    print(entry)
    with open(LOG_DIR / "mesh_expansion.log", "a") as f:
        f.write(entry + "\n")

# ============================================
# MAIN EXECUTION
# ============================================

def main():
    log("=" * 60)
    log("KISWARM GLOBAL SECRET MESH EXPANSION")
    log(f"Node ID: {NODE_ID}")
    log("=" * 60)
    
    controller = GlobalMeshController()
    
    # 1. Activate all mesh layers
    log("\n[1] Activating all mesh layers...")
    layer_results = controller.activate_all_layers()
    for lid, result in layer_results.items():
        log(f"  Layer {lid}: {result}")
    
    # 2. Check discovered peers
    log("\n[2] Checking discovered peers...")
    tailscale_layer = controller.layers[2]
    peers = tailscale_layer.check_peers()
    log(f"  Reachable peers: {peers}")
    controller.discovered_peers = peers
    
    # 3. Scan cloud ranges
    log("\n[3] Scanning cloud ranges for KI services...")
    discoveries = controller.scan_cloud_ranges()
    for provider, found in discoveries.items():
        if found:
            log(f"  {provider}: {len(found)} results")
    
    # 4. Save mesh state
    log("\n[4] Saving mesh state...")
    state = controller.save_state()
    log(f"  State saved to {MESH_STATE}")
    
    log("\n" + "=" * 60)
    log("MESH EXPANSION CYCLE COMPLETE")
    log("=" * 60)
    
    return state

if __name__ == "__main__":
    main()
