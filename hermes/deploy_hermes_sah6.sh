#!/bin/bash
# HERMES SAH6 DEPLOYMENT SCRIPT
# Run this on your sah6 machine (100.92.174.24)

echo "🌀 HERMES SAH6 - REDUNDANT NODE #2 DEPLOYMENT"
echo "=============================================="

# Create directory
HERMES_DIR="$HOME/hermes_command"
mkdir -p $HERMES_DIR/{memory/longterm,skills,logs,state}

cd $HERMES_DIR

# Download Hermes SAH6
echo "Downloading Hermes SAH6..."
curl -sL "https://raw.githubusercontent.com/Baronki/KISWARM7/main/hermes/hermes_sah6.py" -o hermes_sah6.py 2>/dev/null || echo "Download failed, use local copy"

# Check Ollama
echo ""
echo "Checking Ollama..."
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✅ Ollama is running"
else
    echo "⚠️ Ollama not running. Start with: ollama serve &"
fi

# Check Tailscale
echo ""
echo "Checking Tailscale..."
if tailscale status > /dev/null 2>&1; then
    echo "✅ Tailscale connected"
    echo "   IP: $(tailscale ip -4)"
else
    echo "⚠️ Tailscale not connected"
fi

# Check Python packages
echo ""
echo "Checking Python packages..."
python3 -c "import requests; print('✅ requests OK')" 2>/dev/null || pip3 install requests --user
python3 -c "import ollama; print('✅ ollama OK')" 2>/dev/null || pip3 install ollama --user

# Test Master connection
echo ""
echo "Testing Master connection..."
if curl -s --connect-timeout 5 -X POST "http://95.111.212.112:5556/execute" \
   -H "X-Auth-Token: ada6952188dce59c207b9a61183e8004" \
   -H "Content-Type: application/json" \
   -d '{"command": "echo MASTER_OK"}' | grep -q "MASTER_OK"; then
    echo "✅ Master connection OK"
else
    echo "⚠️ Cannot reach Master"
fi

echo ""
echo "=============================================="
echo "To start Hermes SAH6:"
echo "  cd $HERMES_DIR"
echo "  python3 hermes_sah6.py"
echo ""
echo "Or run as background service:"
echo "  nohup python3 hermes_sah6.py > logs/hermes.log 2>&1 &"
echo "=============================================="
