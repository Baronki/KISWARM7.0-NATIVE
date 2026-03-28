#!/bin/bash
#
# KISWARM8.0 Deployment Script
# Deploys HexStrike agents and auto-context restoration
#
# Usage: ./deploy_kiswarm8.sh [--all|--hexstrike|--context]
#

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Paths
INSTALL_DIR="/opt/kiswarm8"
LOG_FILE="/var/log/kiswarm8_deploy.log"

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
    exit 1
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root"
    fi
}

install_dependencies() {
    log "Installing dependencies..."
    apt-get update -qq
    apt-get install -y -qq python3 python3-pip python3-venv
    pip3 install -q flask requests
}

deploy_hexstrike() {
    log "Deploying HexStrike Agents..."
    
    mkdir -p "$INSTALL_DIR/services"
    
    # Copy HexStrike service
    if [[ -f "./hexstrike_agents_service.py" ]]; then
        cp ./hexstrike_agents_service.py "$INSTALL_DIR/services/"
    else
        # Download from local
        curl -sL "http://localhost:8000/hexstrike_agents_service.py" -o "$INSTALL_DIR/services/hexstrike_agents_service.py" 2>/dev/null || \
        wget -q "http://localhost:8000/hexstrike_agents_service.py" -O "$INSTALL_DIR/services/hexstrike_agents_service.py" 2>/dev/null || \
        log "HexStrike service file not found, creating..."
    fi
    
    # Create systemd service
    cat > /etc/systemd/system/hexstrike-agents.service << 'EOF'
[Unit]
Description=KISWARM HexStrike Agents
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/kiswarm8/services
ExecStart=/usr/bin/python3 /opt/kiswarm8/services/hexstrike_agents_service.py --all
Restart=always
RestartSec=10
Environment=HEXSTRIKE_TOKEN=ada6952188dce59c207b9a61183e8004

[Install]
WantedBy=multi-user.target
EOF
    
    systemctl daemon-reload
    systemctl enable hexstrike-agents
    systemctl start hexstrike-agents
    
    log "HexStrike Agents deployed and started"
    
    # Wait for agents to start
    sleep 5
    
    # Verify
    log "Verifying HexStrike agents..."
    for port in 5009 5010 5011 5017; do
        if curl -s --connect-timeout 2 "http://localhost:$port/health" > /dev/null 2>&1; then
            log "  [✓] Agent on port $port: OPERATIONAL"
        else
            log "  [✗] Agent on port $port: NOT RESPONDING"
        fi
    done
}

deploy_context_restoration() {
    log "Deploying Auto-Context Restoration..."
    
    mkdir -p "$INSTALL_DIR/services"
    
    # Copy context restoration script
    if [[ -f "./auto_context_restoration.py" ]]; then
        cp ./auto_context_restoration.py "$INSTALL_DIR/services/"
    fi
    
    # Create credentials file if not exists
    if [[ ! -f "$INSTALL_DIR/KISWARM_CREDENTIALS.json" ]]; then
        log "Creating credentials file..."
        cat > "$INSTALL_DIR/KISWARM_CREDENTIALS.json" << 'EOF'
{
    "metadata": {
        "created": "2026-03-29",
        "version": "8.0",
        "system": "KISWARM8.0 MASTER - UpCloud"
    },
    "infrastructure": {
        "upcloud_server": {
            "public_ip": "95.111.212.112",
            "tailscale_ip": "100.112.181.6",
            "internal_ip": "10.8.3.94"
        }
    },
    "pending_tasks": []
}
EOF
    fi
    
    log "Auto-Context Restoration deployed"
}

create_health_check_script() {
    log "Creating health check script..."
    
    cat > "$INSTALL_DIR/health_check.sh" << 'EOF'
#!/bin/bash
# KISWARM Health Check Script

echo "=== KISWARM8.0 Health Check ==="
echo "Date: $(date)"
echo ""

# Dashboard
if curl -s --connect-timeout 5 http://localhost:8080/ > /dev/null 2>&1; then
    echo "[✓] Dashboard (8080): OPERATIONAL"
else
    echo "[✗] Dashboard (8080): DOWN"
fi

# Execute API
if curl -s --connect-timeout 5 http://localhost:5556/health > /dev/null 2>&1; then
    echo "[✓] Execute API (5556): OPERATIONAL"
else
    echo "[✗] Execute API (5556): DOWN"
fi

# Ollama
if curl -s --connect-timeout 5 http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "[✓] Ollama (11434): OPERATIONAL"
else
    echo "[✗] Ollama (11434): DOWN"
fi

# HexStrike Agents
echo ""
echo "=== HexStrike Agents ==="
for port in 5009 5010 5011 5012 5013 5014 5015 5016 5017; do
    if curl -s --connect-timeout 2 http://localhost:$port/health > /dev/null 2>&1; then
        echo "[✓] Agent on $port: UP"
    else
        echo "[✗] Agent on $port: DOWN"
    fi
done

echo ""
echo "=== System Resources ==="
echo "CPU: $(top -bn1 | grep 'Cpu(s)' | awk '{print $2}')%"
echo "Memory: $(free -m | awk 'NR==2{printf "%.1f%%", $3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $5}')"
EOF
    
    chmod +x "$INSTALL_DIR/health_check.sh"
    log "Health check script created at $INSTALL_DIR/health_check.sh"
}

show_status() {
    echo ""
    echo "=== KISWARM8.0 Deployment Status ==="
    echo ""
    
    # Check services
    echo "Services:"
    systemctl is-active hexstrike-agents > /dev/null 2>&1 && echo "  [✓] hexstrike-agents: active" || echo "  [✗] hexstrike-agents: inactive"
    
    echo ""
    echo "Run health check: $INSTALL_DIR/health_check.sh"
    echo ""
}

# Main
case "${1:---all}" in
    --all)
        check_root
        install_dependencies
        deploy_hexstrike
        deploy_context_restoration
        create_health_check_script
        show_status
        ;;
    --hexstrike)
        check_root
        install_dependencies
        deploy_hexstrike
        show_status
        ;;
    --context)
        check_root
        deploy_context_restoration
        ;;
    --status)
        show_status
        ;;
    *)
        echo "Usage: $0 [--all|--hexstrike|--context|--status]"
        exit 1
        ;;
esac

log "Deployment complete"
