import { NextRequest, NextResponse } from 'next/server'

// AI Models Configuration
const AI_MODELS: Record<string, { name: string; url: string; internalUrl: string }> = {
  'qwen-3.5-abliterated': {
    name: 'Qwen 3.5 Abliterated',
    url: 'http://100.112.181.6:5001',
    internalUrl: 'http://10.8.3.94:5001'
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { model, messages } = body

    if (!model || !messages) {
      return NextResponse.json({ error: 'Missing model or messages' }, { status: 400 })
    }

    const modelConfig = AI_MODELS[model]
    if (!modelConfig) {
      return NextResponse.json({ error: 'Invalid model selection' }, { status: 400 })
    }

    // Try Tailscale URL first, then internal URL
    const urls = [modelConfig.url, modelConfig.internalUrl]
    let lastError: string | null = null

    for (const baseUrl of urls) {
      try {
        // 120 second timeout for long responses
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 120000)

        const response = await fetch(`${baseUrl}/v1/chat/completions`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            model: model,
            messages: messages,
            max_tokens: 4096,
            temperature: 0.7,
            stream: false
          }),
          signal: controller.signal
        })

        clearTimeout(timeoutId)

        if (!response.ok) {
          const errorText = await response.text()
          lastError = `Model API error (${response.status}): ${errorText}`
          continue
        }

        const data = await response.json()
        
        // Extract the response content
        const content = data.choices?.[0]?.message?.content || data.response || data.message || null
        
        if (content) {
          return NextResponse.json({ response: content })
        } else {
          lastError = 'No response content from model'
          continue
        }
      } catch (fetchError) {
        const errorMessage = fetchError instanceof Error ? fetchError.message : 'Unknown fetch error'
        if (errorMessage.includes('abort')) {
          lastError = 'Request timeout (120s limit reached)'
        } else {
          lastError = `Connection error: ${errorMessage}`
        }
        continue
      }
    }

    return NextResponse.json({ error: lastError || 'Failed to connect to AI model' }, { status: 500 })

  } catch (error) {
    console.error('Chat API error:', error)
    return NextResponse.json(
      { error: error instanceof Error ? error.message : 'Internal server error' },
      { status: 500 }
    )
  }
}

export async function GET() {
  return NextResponse.json({
    models: Object.entries(AI_MODELS).map(([id, config]) => ({
      id,
      name: config.name,
      url: config.url
    }))
  })
}
