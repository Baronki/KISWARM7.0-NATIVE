#!/bin/bash
#
# 🚀 KISWARM8.0 AUTONOMOUS DEPLOYMENT SCRIPT
# Deploys all services for 24/7 autonomous operation
#
# Author: Baron Marco Paolo Ialongo - Maquister Equitum
#

set -e

echo "🚀 KISWARM8.0 Autonomous Deployment Starting..."
echo "================================================"

# Configuration
KISWARM_PATH="/opt/kiswarm7"
MODULES_PATH="$KISWARM_PATH/kiswarm_modules"
DATA_PATH="$KISWARM_PATH/data"
LOG_PATH="/var/log/kiswarm"

# Create directories
echo "📁 Creating directories..."
mkdir -p $DATA_PATH
mkdir -p $DATA_PATH/ki_discovery
mkdir -p $LOG_PATH
mkdir -p $KISWARM_PATH/agents

# Update Tor configuration for additional hidden services
echo "🧅 Configuring Tor hidden services..."
cat >> /etc/tor/torrc << 'TORCONF'

# KISWARM Additional Hidden Services
# Qwen Gateway
HiddenServiceDir /var/lib/tor/kiswarm_qwen/
HiddenServicePort 5001 127.0.0.1:5001

# KI Scanner
HiddenServiceDir /var/lib/tor/kiswarm_scanner/
HiddenServicePort 5002 127.0.0.1:5002

# Mesh Orchestrator
HiddenServiceDir /var/lib/tor/kiswarm_orchestrator/
HiddenServicePort 5003 127.0.0.1:5003

TORCONF

# Create systemd service files
echo "⚙️ Creating systemd services..."

# HexStrike Server Service
cat > /etc/systemd/system/kiswarm-hexstrike.service << 'SERVICE'
[Unit]
Description=KISWARM HexStrike Server
After=network.target tor.service
Wants=tor.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
ExecStart=/usr/bin/python3 /opt/kiswarm7/kiswarm_modules/hexstrike_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Qwen Gateway Service
cat > /etc/systemd/system/kiswarm-qwen.service << 'SERVICE'
[Unit]
Description=KISWARM Qwen Tor Gateway
After=network.target tor.service ollama.service
Wants=tor.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
ExecStart=/usr/bin/python3 /opt/kiswarm7/kiswarm_modules/qwen_tor_gateway.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# KI Scanner Service
cat > /etc/systemd/system/kiswarm-scanner.service << 'SERVICE'
[Unit]
Description=KISWARM KI Discovery Scanner
After=network.target tor.service
Wants=tor.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
ExecStart=/usr/bin/python3 /opt/kiswarm7/kiswarm_modules/ki_discovery_scanner.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Mesh Orchestrator Service
cat > /etc/systemd/system/kiswarm-orchestrator.service << 'SERVICE'
[Unit]
Description=KISWARM Mesh Orchestrator
After=network.target tor.service
Wants=tor.service

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
ExecStart=/usr/bin/python3 /opt/kiswarm7/kiswarm_modules/mesh_orchestrator.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Execute API Service
cat > /etc/systemd/system/kiswarm-execute.service << 'SERVICE'
[Unit]
Description=KISWARM Execute API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/kiswarm7
ExecStart=/usr/bin/python3 /opt/kiswarm7/kiswarm_modules/execute_service.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
SERVICE

# Reload systemd
echo "🔄 Reloading systemd..."
systemctl daemon-reload

# Restart Tor to pick up new hidden services
echo "🧅 Restarting Tor..."
systemctl restart tor
sleep 5

# Get onion addresses
echo "📍 Onion Addresses:"
echo "=================="
echo "HexStrike:      $(cat /var/lib/tor/kiswarm8_service/hostname 2>/dev/null || echo 'pending')"
echo "Qwen Gateway:   $(cat /var/lib/tor/kiswarm_qwen/hostname 2>/dev/null || echo 'pending')"
echo "KI Scanner:     $(cat /var/lib/tor/kiswarm_scanner/hostname 2>/dev/null || echo 'pending')"
echo "Orchestrator:   $(cat /var/lib/tor/kiswarm_orchestrator/hostname 2>/dev/null || echo 'pending')"

# Enable and start all services
echo "▶️ Enabling and starting services..."
systemctl enable kiswarm-hexstrike
systemctl enable kiswarm-qwen
systemctl enable kiswarm-scanner
systemctl enable kiswarm-orchestrator
systemctl enable kiswarm-execute

systemctl start kiswarm-hexstrike
systemctl start kiswarm-qwen
systemctl start kiswarm-scanner
systemctl start kiswarm-orchestrator
systemctl start kiswarm-execute

# Wait for services to start
sleep 5

# Check service status
echo ""
echo "📊 Service Status:"
echo "=================="
systemctl is-active kiswarm-hexstrike || echo "hexstrike: FAILED"
systemctl is-active kiswarm-qwen || echo "qwen: FAILED"
systemctl is-active kiswarm-scanner || echo "scanner: FAILED"
systemctl is-active kiswarm-orchestrator || echo "orchestrator: FAILED"
systemctl is-active kiswarm-execute || echo "execute: FAILED"

echo ""
echo "✅ KISWARM8.0 Autonomous Deployment Complete!"
echo ""
echo "🔍 Monitor logs: journalctl -u kiswarm-orchestrator -f"
echo "📊 Status report: curl http://localhost:5003/report"
