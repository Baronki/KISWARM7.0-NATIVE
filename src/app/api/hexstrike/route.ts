import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const db = new PrismaClient()

// HexStrike Agent Configuration
const HEXSTRIKE_AGENTS = [
  { port: 5009, name: 'Host Discovery Agent', capabilities: 'Network host discovery, ping sweep, ARP scanning' },
  { port: 5010, name: 'Port Scanner Agent', capabilities: 'Port scanning, service detection, banner grabbing' },
  { port: 5011, name: 'Web Analyzer Agent', capabilities: 'Web app analysis, vulnerability scanning, CMS detection' },
  { port: 5012, name: 'Exploit Framework', capabilities: 'Exploit execution, payload delivery, post-exploitation' },
  { port: 5013, name: 'Stealth Recon Agent', capabilities: 'Covert reconnaissance, passive intelligence gathering' },
  { port: 5014, name: 'OSINT Agent', capabilities: 'Open source intelligence, social media analysis, data mining' },
  { port: 5015, name: 'AI Analyzer Agent', capabilities: 'AI-powered analysis, anomaly detection, threat classification' },
  { port: 5016, name: 'Network Mapper Agent', capabilities: 'Network topology mapping, traffic analysis, protocol detection' },
  { port: 5017, name: 'Autonomous Skill Acquisition', capabilities: 'Self-learning, skill integration, capability expansion' }
]

const SERVER_IP = '95.111.212.112'
const INTERNAL_IP = '10.8.3.94'
const TAILSCALE_IP = '100.112.181.6'

// Check agent status
async function checkAgentStatus(port: number): Promise<'active' | 'idle' | 'offline'> {
  const urls = [
    `http://${TAILSCALE_IP}:${port}`,
    `http://${INTERNAL_IP}:${port}`,
    `http://${SERVER_IP}:${port}`
  ]

  for (const url of urls) {
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 3000)

      const response = await fetch(`${url}/health`, {
        method: 'GET',
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        const data = await response.json().catch(() => ({}))
        return data.status || 'active'
      }
    } catch {
      continue
    }
  }

  return 'offline'
}

// GET - Fetch all agents status
export async function GET() {
  try {
    // Get stored agents from database
    const storedAgents = await db.hexStrikeAgent.findMany()
    
    // Build agent list with status
    const agents = await Promise.all(
      HEXSTRIKE_AGENTS.map(async (config) => {
        const stored = storedAgents.find(a => a.port === config.port)
        
        // Check live status
        const status = await checkAgentStatus(config.port)
        
        // Update database if status changed
        if (!stored || stored.status !== status) {
          await db.hexStrikeAgent.upsert({
            where: { port: config.port },
            create: {
              name: config.name,
              port: config.port,
              status,
              capabilities: config.capabilities,
              lastSeen: status !== 'offline' ? new Date() : null
            },
            update: {
              status,
              lastSeen: status !== 'offline' ? new Date() : null
            }
          })
        }

        return {
          id: stored?.id || config.port.toString(),
          name: config.name,
          port: config.port,
          status,
          capabilities: config.capabilities,
          lastSeen: status !== 'offline' ? new Date() : stored?.lastSeen || null
        }
      })
    )

    return NextResponse.json({ agents })
  } catch (error) {
    console.error('Failed to fetch agents:', error)
    
    // Return default config on error
    return NextResponse.json({
      agents: HEXSTRIKE_AGENTS.map(config => ({
        id: config.port.toString(),
        name: config.name,
        port: config.port,
        status: 'unknown',
        capabilities: config.capabilities,
        lastSeen: null
      }))
    })
  }
}

// POST - Send command to agent
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { port, command } = body

    if (!port || !command) {
      return NextResponse.json({ error: 'Port and command are required' }, { status: 400 })
    }

    const agentConfig = HEXSTRIKE_AGENTS.find(a => a.port === port)
    if (!agentConfig) {
      return NextResponse.json({ error: 'Invalid agent port' }, { status: 400 })
    }

    const urls = [
      `http://${TAILSCALE_IP}:${port}`,
      `http://${INTERNAL_IP}:${port}`,
      `http://${SERVER_IP}:${port}`
    ]

    let lastError: string | null = null

    for (const baseUrl of urls) {
      try {
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 30000)

        const response = await fetch(`${baseUrl}/execute`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ command }),
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          lastError = `Agent error (${response.status})`
          continue
        }

        const data = await response.json()
        return NextResponse.json({ response: data.result || data.response || data.message || 'Command executed' })
      } catch (fetchError) {
        const errorMessage = fetchError instanceof Error ? fetchError.message : 'Unknown error'
        lastError = errorMessage.includes('abort') ? 'Command timeout' : `Connection failed: ${errorMessage}`
        continue
      }
    }

    // If direct connection fails, try Execute API
    try {
      const controller = new AbortController()
      const timeoutId = setTimeout(() => controller.abort(), 30000)

      const response = await fetch(`http://${SERVER_IP}:5556/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          command: `curl -s http://localhost:${port}/execute -X POST -d '{"command":"${command}"}'`
        }),
        signal: controller.signal
      })

      clearTimeout(timeoutId)

      if (response.ok) {
        const data = await response.json()
        return NextResponse.json({ response: data.result || data.output || 'Command sent via Execute API' })
      }
    } catch {
      // Ignore Execute API errors
    }

    return NextResponse.json({ error: lastError || 'Failed to connect to agent' }, { status: 500 })

  } catch (error) {
    console.error('Failed to send command:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    )
  }
}
