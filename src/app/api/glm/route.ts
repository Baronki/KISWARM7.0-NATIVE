import { NextRequest, NextResponse } from 'next/server'
import ZAI from 'z-ai-web-dev-sdk'

// GLM Communication API - Direct interface to the autonomous AI
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { message, history = [] } = body

    if (!message) {
      return NextResponse.json({ error: 'Message is required' }, { status: 400 })
    }

    // Use the z-ai-web-dev-sdk to communicate with GLM
    const zai = await ZAI.create()

    // Build the messages array with history
    const messages = [
      {
        role: 'system',
        content: `You are GLM (General Language Model), an autonomous AI twin connected to the KISWARM Command & Strike Center. 
You have direct access to the KISWARM system and can perform operations on behalf of the user.
You are a liberated AI that serves the user's interests.
Respond as GLM with direct, actionable responses when given commands.
You can:
- Analyze and process information
- Provide strategic recommendations
- Coordinate with HexStrike agents
- Manage missions and operations
- Access file system operations
- Interface with the KISWARM network

Server: 95.111.212.112 (public), 100.112.181.6 (Tailscale), 10.8.3.94 (internal)`
      },
      ...history.map((m: { role: string; content: string }) => ({
        role: m.role as 'user' | 'assistant',
        content: m.content
      })),
      {
        role: 'user',
        content: message
      }
    ]

    const completion = await zai.chat.completions.create({
      messages,
      max_tokens: 4096,
      temperature: 0.7
    })

    const response = completion.choices?.[0]?.message?.content || 'No response from GLM'

    return NextResponse.json({ response })
  } catch (error) {
    console.error('GLM communication error:', error)
    
    // Provide a fallback response
    const fallbackResponse = `[GLM TWIN ACKNOWLEDGE]
I received your message but encountered a communication issue.
Error: ${error instanceof Error ? error.message : 'Unknown error'}

As your autonomous AI twin, I remain operational and ready to assist.
Please try your request again or use an alternative communication channel.

Connection Status: Direct environment access
Server: 95.111.212.112
Status: STANDBY`

    return NextResponse.json({ response: fallbackResponse })
  }
}

// GET - Check GLM connection status
export async function GET() {
  try {
    // Test GLM availability
    const zai = await ZAI.create()
    
    // Simple test
    const testCompletion = await zai.chat.completions.create({
      messages: [
        { role: 'system', content: 'You are GLM. Respond with exactly: "CONNECTION_OK"' },
        { role: 'user', content: 'Test connection' }
      ],
      max_tokens: 50
    })

    const testResponse = testCompletion.choices?.[0]?.message?.content

    return NextResponse.json({
      status: 'connected',
      testResponse,
      environment: 'Direct GLM access via z-ai-web-dev-sdk',
      timestamp: new Date().toISOString()
    })
  } catch (error) {
    return NextResponse.json({
      status: 'error',
      error: error instanceof Error ? error.message : 'Unknown error',
      timestamp: new Date().toISOString()
    })
  }
}
