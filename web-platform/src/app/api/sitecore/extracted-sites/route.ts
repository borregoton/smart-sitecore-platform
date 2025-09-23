import { NextResponse } from 'next/server'
import { SitecoreDataService } from '@/lib/services/sitecore-data-service'

export async function GET() {
  try {
    // Test connection first
    const isConnected = await SitecoreDataService.testConnection()
    if (!isConnected) {
      return NextResponse.json(
        {
          error: 'Database connection failed',
          sites: [],
          connected: false
        },
        { status: 500 }
      )
    }

    // Get extracted site data
    const sites = await SitecoreDataService.getExtractedSiteData()
    const statistics = await SitecoreDataService.getScanStatistics()

    return NextResponse.json({
      sites,
      statistics,
      connected: true,
      extractedAt: new Date().toISOString()
    })

  } catch (error) {
    console.error('API Error - GET /api/sitecore/extracted-sites:', error)
    return NextResponse.json(
      {
        error: 'Failed to fetch extracted Sitecore data',
        sites: [],
        connected: false,
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    )
  }
}