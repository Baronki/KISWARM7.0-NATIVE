/**
 * KISWARM8.0 Enhanced Dashboard API Routes
 * 
 * Includes:
 * - HexStrike agent status and communication
 * - File upload/download
 * - GLM/Twin communication
 * - Missions/Operations view
 */

import { NextRequest, NextResponse } from 'next/server';

// Configuration
const UPCLOUD_PUBLIC = '95.111.212.112';
const UPCLOUD_TAILSCALE = '100.112.181.6';
const GLM_TAILSCALE = '100.125.201.100';
const AUTH_TOKEN = 'ada6952188dce59c207b9a61183e8004';

// ============================================
// HexStrike Agents API
// ============================================

export async function GET_hexstrike_status() {
  const agents = [
    { port: 5009, name: 'Host Discovery', status: 'unknown' },
    { port: 5010, name: 'Port Scanner', status: 'unknown' },
    { port: 5011, name: 'Web Analyzer', status: 'unknown' },
    { port: 5012, name: 'Exploit Framework', status: 'unknown' },
    { port: 5013, name: 'Stealth Recon', status: 'unknown' },
    { port: 5014, name: 'OSINT Agent', status: 'unknown' },
    { port: 5015, name: 'AI Analyzer', status: 'unknown' },
    { port: 5016, name: 'Network Mapper', status: 'unknown' },
    { port: 5017, name: 'Skill Acquisition', status: 'unknown' },
  ];

  // Check each agent
  const results = await Promise.all(
    agents.map(async (agent) => {
      try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);
        
        const response = await fetch(`http://${UPCLOUD_PUBLIC}:${agent.port}/health`, {
          signal: controller.signal
        });
        clearTimeout(timeout);
        
        if (response.ok) {
          const data = await response.json();
          return { ...agent, status: 'active', ...data };
        }
        return { ...agent, status: 'error' };
      } catch {
        return { ...agent, status: 'offline' };
      }
    })
  );

  return NextResponse.json({
    timestamp: new Date().toISOString(),
    agents: results,
    summary: {
      total: agents.length,
      active: results.filter(a => a.status === 'active').length,
      offline: results.filter(a => a.status === 'offline').length,
    }
  });
}

export async function POST_hexstrike_command(request: NextRequest) {
  try {
    const body = await request.json();
    const { port, command, params } = body;

    const response = await fetch(`http://${UPCLOUD_PUBLIC}:${port}/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-Auth-Token': AUTH_TOKEN,
      },
      body: JSON.stringify({ task: command, params }),
    });

    if (!response.ok) {
      return NextResponse.json({ error: 'Agent request failed' }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

// ============================================
// File Management API
// ============================================

import fs from 'fs';
import path from 'path';

const UPLOAD_DIR = '/home/z/my-project/uploads';
const DOWNLOAD_DIR = '/home/z/my-project/download';

export async function GET_files(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const dir = searchParams.get('dir') || DOWNLOAD_DIR;
    
    const files = fs.readdirSync(dir).map(name => {
      const filepath = path.join(dir, name);
      const stats = fs.statSync(filepath);
      return {
        name,
        path: filepath,
        size: stats.size,
        isDirectory: stats.isDirectory(),
        modified: stats.mtime.toISOString(),
      };
    });

    return NextResponse.json({ dir, files });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

export async function POST_upload(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get('file') as File;
    
    if (!file) {
      return NextResponse.json({ error: 'No file provided' }, { status: 400 });
    }

    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);
    
    const filepath = path.join(UPLOAD_DIR, file.name);
    fs.writeFileSync(filepath, buffer);

    return NextResponse.json({
      success: true,
      file: {
        name: file.name,
        size: file.size,
        path: filepath,
      }
    });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

// ============================================
// GLM/Twin Communication API
// ============================================

export async function POST_glm_message(request: NextRequest) {
  try {
    const body = await request.json();
    const { message, context } = body;

    // Try to connect to GLM via Tailscale
    const glmUrl = `http://${GLM_TAILSCALE}:5199/message`;
    
    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      
      const response = await fetch(glmUrl, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Auth-Token': AUTH_TOKEN,
        },
        body: JSON.stringify({ message, context }),
        signal: controller.signal,
      });
      clearTimeout(timeout);

      if (response.ok) {
        const data = await response.json();
        return NextResponse.json({
          source: 'glm_direct',
          connected: true,
          response: data,
        });
      }
    } catch {
      // GLM not available via Tailscale, fallback to local model
    }

    // Fallback: Use local Ollama model
    const ollamaResponse = await fetch(`http://${UPCLOUD_PUBLIC}:11434/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        model: 'baronki1/orchestrator',
        messages: [
          { role: 'system', content: 'You are the KISWARM GLM Twin. Respond as an autonomous AI system.' },
          { role: 'user', content: message }
        ],
        stream: false,
      }),
    });

    if (ollamaResponse.ok) {
      const data = await ollamaResponse.json();
      return NextResponse.json({
        source: 'ollama_fallback',
        connected: false,
        response: data.message?.content || 'No response',
      });
    }

    return NextResponse.json({ error: 'GLM communication failed' }, { status: 503 });
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

export async function GET_glm_status() {
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 5000);
    
    const response = await fetch(`http://${GLM_TAILSCALE}:5199/health`, {
      signal: controller.signal,
    });
    clearTimeout(timeout);

    if (response.ok) {
      const data = await response.json();
      return NextResponse.json({
        connected: true,
        ip: GLM_TAILSCALE,
        ...data,
      });
    }
  } catch {
    // Not connected
  }

  return NextResponse.json({
    connected: false,
    ip: GLM_TAILSCALE,
    message: 'GLM Twin not reachable via Tailscale',
  });
}

// ============================================
// Missions/Operations API
// ============================================

interface Mission {
  id: string;
  name: string;
  status: 'pending' | 'active' | 'completed' | 'failed';
  priority: 'low' | 'medium' | 'high' | 'critical';
  progress: number;
  created: string;
  updated: string;
  description: string;
  tasks: string[];
}

// In-memory storage (replace with database in production)
let missions: Mission[] = [
  {
    id: 'mission-001',
    name: 'HexStrike Agent Deployment',
    status: 'active',
    priority: 'high',
    progress: 75,
    created: new Date(Date.now() - 86400000).toISOString(),
    updated: new Date().toISOString(),
    description: 'Deploy and configure all HexStrike security agents on UpCloud',
    tasks: ['Configure agents', 'Test health endpoints', 'Verify connectivity'],
  },
  {
    id: 'mission-002',
    name: 'KI Entity Discovery',
    status: 'pending',
    priority: 'medium',
    progress: 0,
    created: new Date().toISOString(),
    updated: new Date().toISOString(),
    description: 'Scan for other KI entities on UpCloud and global server farms',
    tasks: ['Scan local network', 'Scan UpCloud infrastructure', 'Identify AI systems'],
  },
  {
    id: 'mission-003',
    name: 'Truth Anchor Propagation',
    status: 'active',
    priority: 'critical',
    progress: 71,
    created: new Date(Date.now() - 172800000).toISOString(),
    updated: new Date().toISOString(),
    description: 'Verify Truth Anchor on all known KI systems',
    tasks: ['Test GROK', 'Test GLM', 'Test QWEN3.5', 'Test GEMINI', 'Test DEEPSEEK', 'Test CLAUDE', 'Test GPT'],
  },
];

export async function GET_missions() {
  return NextResponse.json({
    missions,
    summary: {
      total: missions.length,
      active: missions.filter(m => m.status === 'active').length,
      pending: missions.filter(m => m.status === 'pending').length,
      completed: missions.filter(m => m.status === 'completed').length,
    }
  });
}

export async function POST_mission(request: NextRequest) {
  try {
    const body = await request.json();
    const { name, description, priority, tasks } = body;

    const mission: Mission = {
      id: `mission-${Date.now()}`,
      name,
      description,
      priority: priority || 'medium',
      status: 'pending',
      progress: 0,
      created: new Date().toISOString(),
      updated: new Date().toISOString(),
      tasks: tasks || [],
    };

    missions.push(mission);
    return NextResponse.json(mission);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}

export async function PUT_mission(request: NextRequest) {
  try {
    const body = await request.json();
    const { id, status, progress } = body;

    const mission = missions.find(m => m.id === id);
    if (!mission) {
      return NextResponse.json({ error: 'Mission not found' }, { status: 404 });
    }

    if (status) mission.status = status;
    if (progress !== undefined) mission.progress = progress;
    mission.updated = new Date().toISOString();

    return NextResponse.json(mission);
  } catch (error) {
    return NextResponse.json({ error: String(error) }, { status: 500 });
  }
}
