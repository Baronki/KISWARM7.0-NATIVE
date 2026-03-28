import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'

const db = new PrismaClient()

// GET - Fetch all missions
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const missionId = searchParams.get('id')

    if (missionId) {
      const mission = await db.mission.findUnique({
        where: { id: missionId },
        include: { logs: { orderBy: { timestamp: 'desc' }, take: 50 } }
      })
      return NextResponse.json({ mission })
    }

    const missions = await db.mission.findMany({
      include: { logs: { orderBy: { timestamp: 'desc' }, take: 10 } },
      orderBy: { createdAt: 'desc' }
    })

    return NextResponse.json({ missions })
  } catch (error) {
    console.error('Failed to fetch missions:', error)
    return NextResponse.json(
      { error: 'Failed to fetch missions' },
      { status: 500 }
    )
  }
}

// POST - Create new mission
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { name, description, status, priority, assignedTo } = body

    if (!name) {
      return NextResponse.json({ error: 'Mission name is required' }, { status: 400 })
    }

    const mission = await db.mission.create({
      data: {
        name,
        description: description || null,
        status: status || 'pending',
        priority: priority || 'medium',
        assignedTo: assignedTo || null,
        startTime: status === 'active' ? new Date() : null
      }
    })

    // Create initial log
    await db.missionLog.create({
      data: {
        missionId: mission.id,
        message: `Mission "${name}" created`,
        level: 'info'
      }
    })

    return NextResponse.json({ mission })
  } catch (error) {
    console.error('Failed to create mission:', error)
    return NextResponse.json(
      { error: 'Failed to create mission' },
      { status: 500 }
    )
  }
}

// PUT - Update mission
export async function PUT(request: NextRequest) {
  try {
    const body = await request.json()
    const { id, status, progress, name, description, priority, assignedTo } = body

    if (!id) {
      return NextResponse.json({ error: 'Mission ID is required' }, { status: 400 })
    }

    const updateData: Record<string, unknown> = {}
    
    if (status !== undefined) {
      updateData.status = status
      if (status === 'active' && !(await db.mission.findUnique({ where: { id } }))?.startTime) {
        updateData.startTime = new Date()
      }
      if (status === 'completed' || status === 'failed') {
        updateData.endTime = new Date()
      }
    }
    if (progress !== undefined) updateData.progress = progress
    if (name !== undefined) updateData.name = name
    if (description !== undefined) updateData.description = description
    if (priority !== undefined) updateData.priority = priority
    if (assignedTo !== undefined) updateData.assignedTo = assignedTo

    const mission = await db.mission.update({
      where: { id },
      data: updateData
    })

    // Create status change log
    if (status) {
      await db.missionLog.create({
        data: {
          missionId: id,
          message: `Mission status changed to: ${status}`,
          level: status === 'completed' ? 'success' : status === 'failed' ? 'error' : 'info'
        }
      })
    }

    return NextResponse.json({ mission })
  } catch (error) {
    console.error('Failed to update mission:', error)
    return NextResponse.json(
      { error: 'Failed to update mission' },
      { status: 500 }
    )
  }
}

// DELETE - Delete mission
export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json({ error: 'Mission ID is required' }, { status: 400 })
    }

    await db.mission.delete({ where: { id } })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to delete mission:', error)
    return NextResponse.json(
      { error: 'Failed to delete mission' },
      { status: 500 }
    )
  }
}
