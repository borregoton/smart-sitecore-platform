import { useState, useEffect } from 'react'
import { ExtractedSiteData } from '@/lib/services/sitecore-data-service'

export interface SitecoreStatistics {
  totalScans: number
  successfulScans: number
  averageConfidence: number
  totalSitesDiscovered: number
  lastScanDate?: string
}

export interface SitecoreDataResponse {
  sites: ExtractedSiteData[]
  statistics: SitecoreStatistics
  connected: boolean
  extractedAt: string
}

export function useSitecoreData() {
  const [data, setData] = useState<SitecoreDataResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchSitecoreData = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/sitecore/extracted-sites')
      if (!response.ok) {
        throw new Error('Failed to fetch Sitecore data')
      }

      const result = await response.json()
      setData(result)

      if (!result.connected) {
        setError('Database connection failed')
      }

    } catch (err) {
      console.error('Error fetching Sitecore data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch Sitecore data')
      setData(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchSitecoreData()
  }, [])

  return {
    data,
    sites: data?.sites || [],
    statistics: data?.statistics || null,
    connected: data?.connected || false,
    loading,
    error,
    refetch: fetchSitecoreData
  }
}

export function useTriggerExtraction() {
  const [triggering, setTriggering] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const triggerExtraction = async (): Promise<boolean> => {
    try {
      setTriggering(true)
      setError(null)

      const response = await fetch('/api/sitecore/trigger-extraction', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        }
      })

      if (!response.ok) {
        throw new Error('Failed to trigger extraction')
      }

      const result = await response.json()

      if (!result.success) {
        throw new Error(result.error || 'Extraction failed')
      }

      return true

    } catch (err) {
      console.error('Error triggering extraction:', err)
      setError(err instanceof Error ? err.message : 'Failed to trigger extraction')
      return false
    } finally {
      setTriggering(false)
    }
  }

  return {
    triggerExtraction,
    triggering,
    error
  }
}