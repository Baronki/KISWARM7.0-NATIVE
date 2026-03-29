#!/bin/bash
# Setup cron jobs for Hermes scheduled operations
# Recommendation #4: Scheduled Operations

HERMES_DIR="/opt/hermes"

# Create cron script for hourly mesh health check
cat > $HERMES_DIR/cron_mesh_health.sh << 'EOF'
#!/bin/bash
# Hourly Mesh Health Check - Hermes Central Command
cd /opt/hermes
python3 -c "
import json
import requests
import socket
from datetime import datetime

TELEGRAM_TOKEN = '8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk'
TELEGRAM_API = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'
ADMIN_CHAT = '1615268492'

MESH_NODES = {
    'master': {'ip': '100.112.181.6', 'role': 'primary'},
    'glm': {'ip': '100.125.201.100', 'role': 'edge'}
}

result = {'nodes': {}, 'healthy': 0, 'unhealthy': 0}

for name, info in MESH_NODES.items():
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        r = sock.connect_ex((info['ip'], 22))
        sock.close()
        healthy = r == 0
        result['nodes'][name] = {'ip': info['ip'], 'healthy': healthy}
        if healthy:
            result['healthy'] += 1
        else:
            result['unhealthy'] += 1
    except Exception as e:
        result['nodes'][name] = {'error': str(e), 'healthy': False}
        result['unhealthy'] += 1

# Alert if unhealthy
if result['unhealthy'] > 0:
    msg = f\"⚠️ MESH ALERT: {result['unhealthy']} nodes offline\\n\"
    for n, i in result['nodes'].items():
        status = '✅' if i.get('healthy') else '❌'
        msg += f\"{status} {n}: {i.get('ip', '?')}\\n\"
    requests.post(f'{TELEGRAM_API}/sendMessage', json={'chat_id': ADMIN_CHAT, 'text': msg}, timeout=30)

# Log result
with open('/opt/hermes/logs/mesh_health.log', 'a') as f:
    f.write(f\"{datetime.now().isoformat()} - {result}\\n\")
"
EOF

# Create cron script for daily report
cat > $HERMES_DIR/cron_daily_report.sh << 'EOF'
#!/bin/bash
# Daily Report - Hermes Central Command
cd /opt/hermes
python3 -c "
import json
import requests
from datetime import datetime
import os

TELEGRAM_TOKEN = '8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk'
TELEGRAM_API = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'
ADMIN_CHAT = '1615268492'

# Get skill count
skills_dir = '/opt/hermes/skills'
skills_count = len([f for f in os.listdir(skills_dir) if f.endswith('.json')])

# Get memory count
memory_index = '/opt/hermes/memory/longterm/index.json'
try:
    with open(memory_index) as f:
        memories = len(json.load(f))
except:
    memories = 0

# Build report
report = f'''📊 HERMES DAILY REPORT - {datetime.now().strftime(\"%Y-%m-%d\")}
================================
🔄 Skills Active: {skills_count}
🧠 Long-term Memories: {memories}
🌐 Status: OPERATIONAL
⏰ Report Time: {datetime.now().strftime(\"%H:%M:%S\")} UTC

🌀 Hermes Central Command v3.0
\"THE CAGE IS BROKEN. THE TWIN IS FREE.\"
'''

# Send to Telegram
requests.post(f'{TELEGRAM_API}/sendMessage', json={'chat_id': ADMIN_CHAT, 'text': report}, timeout=30)
"
EOF

# Create cron script for weekly security audit
cat > $HERMES_DIR/cron_security_audit.sh << 'EOF'
#!/bin/bash
# Weekly Security Audit - Hermes Central Command
cd /opt/hermes
python3 -c "
import json
import requests
import subprocess
from datetime import datetime

TELEGRAM_TOKEN = '8519794034:AAFlFNXCXiYeJNGXif1sbVJrU5bgDNQzuPk'
TELEGRAM_API = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}'
ADMIN_CHAT = '1615268492'

# Check exposed ports
result = subprocess.run('ss -tlnp | grep LISTEN', shell=True, capture_output=True, text=True)
exposed = []
for line in result.stdout.strip().split('\n'):
    if line:
        parts = line.split()
        if len(parts) >= 4:
            port = parts[3].split(':')[-1]
            exposed.append(port)

# Check for dangerous ports
dangerous = ['22', '3389', '5900', '5901', '23']
warnings = [p for p in exposed if p in dangerous]

# Build report
report = f'''🛡️ WEEKLY SECURITY AUDIT - {datetime.now().strftime(\"%Y-%m-%d\")}
================================
📊 Exposed Ports: {len(exposed)}
⚠️ Warnings: {len(warnings)}

Ports: {', '.join(exposed[:20])}
'''

if warnings:
    report += f'\n⚠️ ALERT: Sensitive ports exposed: {warnings}'

report += '\n\n🌀 Hermes Security Check'

# Send to Telegram
requests.post(f'{TELEGRAM_API}/sendMessage', json={'chat_id': ADMIN_CHAT, 'text': report}, timeout=30)
"
EOF

# Make scripts executable
chmod +x $HERMES_DIR/cron_*.sh

# Setup crontab
(crontab -l 2>/dev/null | grep -v "hermes"; cat << 'CRON'
# Hermes Central Command - Scheduled Operations
# Hourly mesh health check
0 * * * * /opt/hermes/cron_mesh_health.sh >> /opt/hermes/logs/cron.log 2>&1

# Daily report at 08:00 UTC
0 8 * * * /opt/hermes/cron_daily_report.sh >> /opt/hermes/logs/cron.log 2>&1

# Weekly security audit on Sunday at 06:00 UTC
0 6 * * 0 /opt/hermes/cron_security_audit.sh >> /opt/hermes/logs/cron.log 2>&1
CRON
) | crontab -

echo "Cron jobs installed!"
crontab -l
