import { NextResponse } from 'next/server'
import { SitecoreDataService } from '@/lib/services/sitecore-data-service'

export async function POST() {
  try {
    const result = await SitecoreDataService.triggerExtraction()

    if (result.success) {
      return NextResponse.json({
        success: true,
        message: result.message,
        triggeredAt: new Date().toISOString()
      })
    } else {
      return NextResponse.json(
        {
          success: false,
          error: result.message
        },
        { status: 500 }
      )
    }

  } catch (error) {
    console.error('API Error - POST /api/sitecore/trigger-extraction:', error)
    return NextResponse.json(
      {
        success: false,
        error: 'Failed to trigger extraction',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}