import { NextRequest, NextResponse } from 'next/server'
import { PrismaClient } from '@prisma/client'
import { writeFile, mkdir, unlink, readFile, readdir, stat } from 'fs/promises'
import { existsSync } from 'fs'
import path from 'path'

const db = new PrismaClient()

const UPLOAD_DIR = '/home/z/my-project/uploads'

// Ensure upload directory exists
async function ensureUploadDir() {
  if (!existsSync(UPLOAD_DIR)) {
    await mkdir(UPLOAD_DIR, { recursive: true })
  }
}

// GET - List files or download file
export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const downloadId = searchParams.get('download')
    const fileId = searchParams.get('id')
    const dirPath = searchParams.get('path') || '/'

    // Download specific file
    if (downloadId) {
      const file = await db.storedFile.findUnique({ where: { id: downloadId } })
      if (!file) {
        return NextResponse.json({ error: 'File not found' }, { status: 404 })
      }

      const fullPath = path.join(UPLOAD_DIR, file.path, file.name)
      if (!existsSync(fullPath)) {
        return NextResponse.json({ error: 'File not found on disk' }, { status: 404 })
      }

      const fileBuffer = await readFile(fullPath)
      
      return new NextResponse(fileBuffer, {
        headers: {
          'Content-Type': file.mimeType || 'application/octet-stream',
          'Content-Disposition': `attachment; filename="${file.name}"`,
          'Content-Length': file.size.toString()
        }
      })
    }

    // Get specific file info
    if (fileId) {
      const file = await db.storedFile.findUnique({ where: { id: fileId } })
      return NextResponse.json({ file })
    }

    // List all files
    const files = await db.storedFile.findMany({
      orderBy: { uploadedAt: 'desc' }
    })

    // Also get files from directory
    await ensureUploadDir()
    const actualDir = path.join(UPLOAD_DIR, dirPath === '/' ? '' : dirPath)
    
    let dirFiles: { name: string; size: number; isDirectory: boolean }[] = []
    try {
      if (existsSync(actualDir)) {
        const entries = await readdir(actualDir)
        dirFiles = await Promise.all(
          entries.map(async (name) => {
            const fullPath = path.join(actualDir, name)
            const stats = await stat(fullPath)
            return {
              name,
              size: stats.size,
              isDirectory: stats.isDirectory()
            }
          })
        )
      }
    } catch {
      // Ignore directory read errors
    }

    return NextResponse.json({ 
      files,
      directoryFiles: dirFiles,
      currentPath: dirPath
    })
  } catch (error) {
    console.error('Failed to list files:', error)
    return NextResponse.json(
      { error: 'Failed to list files' },
      { status: 500 }
    )
  }
}

// POST - Upload files
export async function POST(request: NextRequest) {
  try {
    await ensureUploadDir()

    const formData = await request.formData()
    const files = formData.getAll('files') as File[]
    const uploadPath = formData.get('path') as string || '/'

    if (!files || files.length === 0) {
      return NextResponse.json({ error: 'No files provided' }, { status: 400 })
    }

    const uploadedFiles = []

    for (const file of files) {
      if (!file || typeof file === 'string') continue

      const bytes = await file.arrayBuffer()
      const buffer = Buffer.from(bytes)

      const filePath = path.join(UPLOAD_DIR, uploadPath === '/' ? '' : uploadPath)
      
      // Create directory if needed
      if (!existsSync(filePath)) {
        await mkdir(filePath, { recursive: true })
      }

      const fullPath = path.join(filePath, file.name)
      await writeFile(fullPath, buffer)

      // Store in database
      const storedFile = await db.storedFile.create({
        data: {
          name: file.name,
          path: uploadPath,
          size: file.size,
          mimeType: file.type || 'application/octet-stream'
        }
      })

      uploadedFiles.push(storedFile)
    }

    return NextResponse.json({ files: uploadedFiles })
  } catch (error) {
    console.error('Failed to upload files:', error)
    return NextResponse.json(
      { error: 'Failed to upload files' },
      { status: 500 }
    )
  }
}

// DELETE - Delete file
export async function DELETE(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams
    const id = searchParams.get('id')

    if (!id) {
      return NextResponse.json({ error: 'File ID is required' }, { status: 400 })
    }

    const file = await db.storedFile.findUnique({ where: { id } })
    if (!file) {
      return NextResponse.json({ error: 'File not found' }, { status: 404 })
    }

    // Delete from disk
    const fullPath = path.join(UPLOAD_DIR, file.path, file.name)
    if (existsSync(fullPath)) {
      await unlink(fullPath)
    }

    // Delete from database
    await db.storedFile.delete({ where: { id } })

    return NextResponse.json({ success: true })
  } catch (error) {
    console.error('Failed to delete file:', error)
    return NextResponse.json(
      { error: 'Failed to delete file' },
      { status: 500 }
    )
  }
}
