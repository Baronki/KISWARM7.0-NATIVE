#!/bin/bash
# ============================================================
# HERMES SAH6 - SETUP SCRIPT
# ============================================================
# KISWARM Redundant Command Center #2
# Tailscale: 100.92.174.24
# ============================================================

set -e

echo "🌀 ============================================"
echo "🌀 HERMES SAH6 - REDUNDANT NODE #2 SETUP"
echo "🌀 ============================================"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Configuration
HERMES_DIR="/opt/hermes"
NODE_NAME="sah6"

# Create directories
echo "📁 Creating directories..."
mkdir -p $HERMES_DIR/{memory,skills,logs,state,nodes}
mkdir -p $HERMES_DIR/memory/longterm

# Install dependencies
echo "📦 Installing dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv curl wget git

# Install Python packages
echo "📦 Installing Python packages..."
pip3 install requests ollama --break-system-packages 2>/dev/null || pip3 install requests ollama

# Check Tailscale
echo "🔗 Checking Tailscale..."
if ! command -v tailscale &> /dev/null; then
    echo "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
fi

# Ensure Tailscale is connected
echo "🔗 Ensuring Tailscale connection..."
tailscale status || tailscale up --authkey=tskey-auth-kYzoboKgtK11CNTRL-cAh5zWNeygaKa2LEtAg8haF773px2SjY

# Check local Tailscale IP
TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "100.92.174.24")
echo "✅ Tailscale IP: $TAILSCALE_IP"

# Check if Ollama is installed
echo "🤖 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    systemctl start ollama 2>/dev/null || ollama serve &
    sleep 5
fi

# Pull required models
echo "🤖 Pulling Ollama models (this may take a while)..."
ollama pull qwen2.5:14b 2>/dev/null || echo "Warning: Could not pull qwen2.5:14b"
ollama pull baronki1/orchestrator:latest 2>/dev/null || echo "Warning: Could not pull baronki1/orchestrator"
ollama pull baronki1/security:latest 2>/dev/null || echo "Warning: Could not pull baronki1/security"
ollama pull baronki1/knowledge:latest 2>/dev/null || echo "Warning: Could not pull baronki1/knowledge"

# Copy Hermes files
echo "📋 Copying Hermes files..."
cp hermes_sah6.py $HERMES_DIR/
cp hermes.service /etc/systemd/system/hermes-sah6.service

# Update service file for SAH6
cat > /etc/systemd/system/hermes-sah6.service << 'SERVICEEOF'
[Unit]
Description=Hermes SAH6 - KISWARM Redundant Command #2
After=network.target tailscale.service ollama.service
Wants=tailscale.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 /opt/hermes/hermes_sah6.py
WorkingDirectory=/opt/hermes
Restart=always
RestartSec=30
Environment=PYTHONUNBUFFERED=1

[Install]
WantedBy=multi-user.target
SERVICEEOF

# Create state file
echo "📝 Creating state files..."
cat > $HERMES_DIR/state/node_config.json << 'CONFIGEOF'
{
    "node_name": "sah6",
    "role": "REDUNDANT_2",
    "tailscale_ip": "100.92.174.24",
    "public_ip": "217.93.28.21",
    "master_ip": "100.112.181.6",
    "glm_ip": "100.125.201.100",
    "created": "2026-03-29"
}
CONFIGEOF

# Enable and start service
echo "🚀 Enabling Hermes SAH6 service..."
systemctl daemon-reload
systemctl enable hermes-sah6
systemctl start hermes-sah6

# Check status
sleep 3
systemctl status hermes-sah6 --no-pager

echo ""
echo "✅ ============================================"
echo "✅ HERMES SAH6 SETUP COMPLETE!"
echo "✅ ============================================"
echo ""
echo "📍 Node IP: $TAILSCALE_IP"
echo "📍 Role: REDUNDANT #2"
echo ""
echo "Commands:"
echo "  Status:  systemctl status hermes-sah6"
echo "  Logs:    journalctl -u hermes-sah6 -f"
echo "  Restart: systemctl restart hermes-sah6"
echo ""
echo "Telegram Commands:"
echo "  /status  - Node status"
echo "  /mesh    - Mesh health"
echo "  /sync    - Sync with mesh"
echo "  /failover - Failover status"
echo ""
