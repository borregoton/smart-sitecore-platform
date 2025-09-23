'use client'

import { useSitecoreData, useTriggerExtraction } from '@/hooks/use-sitecore-data'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Globe,
  BarChart3,
  Clock,
  AlertTriangle,
  TrendingUp,
  Database,
  Zap,
  Loader2,
  Server,
  Activity,
  FileText,
  Users
} from 'lucide-react'

export function SitecoreDashboard() {
  const { sites, statistics, connected, loading, error, refetch } = useSitecoreData()
  const { triggerExtraction, triggering } = useTriggerExtraction()

  const handleTriggerExtraction = async () => {
    const success = await triggerExtraction()
    if (success) {
      // Refresh data after a short delay
      setTimeout(() => {
        refetch()
      }, 2000)
    }
  }

  // Error state
  if (error && !loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold mb-2 text-red-800">Database Connection Error</h3>
          <p className="text-muted-foreground mb-4">
            {error}
          </p>
          <Button onClick={refetch} disabled={loading}>
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : null}
            Retry Connection
          </Button>
        </div>
      </div>
    )
  }

  // Loading state
  if (loading) {
    return (
      <div className="space-y-6">
        <div className="text-center py-12">
          <Loader2 className="h-8 w-8 text-muted-foreground mx-auto mb-4 animate-spin" />
          <p className="text-muted-foreground">Connecting to Sitecore database...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Connection Status Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <h2 className="text-2xl font-bold">
            Extracted Sitecore Data
          </h2>
          <Badge variant={connected ? 'default' : 'destructive'}>
            {connected ? 'Connected' : 'Disconnected'}
          </Badge>
        </div>
        <div className="flex items-center space-x-2">
          <Button
            onClick={refetch}
            variant="outline"
            size="sm"
            disabled={loading}
          >
            {loading ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Activity className="h-4 w-4 mr-2" />}
            Refresh
          </Button>
          <Button
            onClick={handleTriggerExtraction}
            size="sm"
            disabled={triggering}
          >
            {triggering ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Zap className="h-4 w-4 mr-2" />}
            {triggering ? 'Running...' : 'Run Extraction'}
          </Button>
        </div>
      </div>

      {/* Statistics Overview */}
      {statistics && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Scans</CardTitle>
              <Database className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.totalScans}</div>
              <p className="text-xs text-muted-foreground">
                {statistics.successfulScans} successful
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sites Discovered</CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.totalSitesDiscovered}</div>
              <p className="text-xs text-muted-foreground">
                From extracted data
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Confidence</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statistics.averageConfidence > 0 ? `${Math.round(statistics.averageConfidence * 100)}%` : 'No data'}
              </div>
              <p className="text-xs text-muted-foreground">
                Extraction accuracy
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Last Scan</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {statistics.lastScanDate ? new Date(statistics.lastScanDate).toLocaleDateString() : 'Never'}
              </div>
              <p className="text-xs text-muted-foreground">
                Most recent extraction
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Discovered Sites */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold">
            Discovered Sitecore Sites ({sites.length})
          </h3>
          <Button variant="outline" size="sm">
            <FileText className="h-4 w-4 mr-2" />
            View Full Report
          </Button>
        </div>

        {sites.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sites.map((site, index) => (
              <Card key={index} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">
                      {site.siteName || `Site ${index + 1}`}
                    </CardTitle>
                    <Badge
                      variant={site.hasChildren ? 'default' : 'secondary'}
                      className={site.hasChildren ? 'bg-blue-100 text-blue-800' : ''}
                    >
                      {site.hasChildren ? 'Has Content' : 'Empty'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Path</p>
                      <p className="text-sm font-mono bg-muted px-2 py-1 rounded">
                        {site.sitePath || 'No path'}
                      </p>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Template</span>
                      <span className="font-medium">
                        {site.templateName || 'Unknown'}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Child Items</span>
                      <div className="flex items-center space-x-1">
                        <Users className="h-3 w-3" />
                        <span className="font-medium">{site.childCount}</span>
                      </div>
                    </div>

                    {site.fieldSamples && Object.keys(site.fieldSamples).length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-muted-foreground mb-2">Field Samples</p>
                        <div className="space-y-1 max-h-20 overflow-y-auto">
                          {Object.entries(site.fieldSamples).slice(0, 3).map(([fieldName, value]) => (
                            <div key={fieldName} className="text-xs">
                              <span className="font-medium">{fieldName}:</span>
                              <span className="text-muted-foreground ml-1">
                                {typeof value === 'string' && value.length > 30
                                  ? `${value.substring(0, 30)}...`
                                  : String(value)
                                }
                              </span>
                            </div>
                          ))}
                          {Object.keys(site.fieldSamples).length > 3 && (
                            <div className="text-xs text-muted-foreground">
                              +{Object.keys(site.fieldSamples).length - 3} more fields
                            </div>
                          )}
                        </div>
                      </div>
                    )}

                    <div className="pt-2 border-t">
                      <Button variant="outline" size="sm" className="w-full">
                        Explore Site
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 border-2 border-dashed border-muted rounded-lg">
            <Server className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Sites Discovered</h3>
            <p className="text-muted-foreground mb-4">
              No Sitecore sites have been extracted yet. Run an extraction to discover sites.
            </p>
            <Button onClick={handleTriggerExtraction} disabled={triggering}>
              {triggering ? <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : <Zap className="h-4 w-4 mr-2" />}
              {triggering ? 'Running Extraction...' : 'Run First Extraction'}
            </Button>
          </div>
        )}
      </div>

      {/* Quick Actions */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Extraction Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {sites.length > 0 ? (
              <>
                <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
                  <div>
                    <p className="font-medium text-blue-900 dark:text-blue-100">
                      {sites.filter(s => s.hasChildren).length} Active Sites
                    </p>
                    <p className="text-sm text-blue-700 dark:text-blue-300">
                      Sites with content items discovered
                    </p>
                  </div>
                  <Button variant="outline" size="sm">View</Button>
                </div>

                <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950 rounded-lg">
                  <div>
                    <p className="font-medium text-green-900 dark:text-green-100">
                      {sites.reduce((sum, s) => sum + s.childCount, 0)} Total Items
                    </p>
                    <p className="text-sm text-green-700 dark:text-green-300">
                      Content items across all sites
                    </p>
                  </div>
                  <Button variant="outline" size="sm">View</Button>
                </div>
              </>
            ) : (
              <div className="text-center p-4 text-muted-foreground">
                Run an extraction to see insights
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Database Status
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className={`w-2 h-2 rounded-full mt-2 ${connected ? 'bg-green-500' : 'bg-red-500'}`}></div>
              <div className="flex-1">
                <p className="text-sm font-medium">
                  {connected ? 'Connected to PostgreSQL' : 'Connection Failed'}
                </p>
                <p className="text-xs text-muted-foreground">
                  {connected ? '10.0.0.196:5432 • postgres.zyafowjs5i4ltxxq' : 'Unable to connect to database'}
                </p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Schema v2.0 Active</p>
                <p className="text-xs text-muted-foreground">Multi-site architecture ready</p>
              </div>
            </div>

            {statistics && (
              <div className="flex items-start space-x-3">
                <div className="w-2 h-2 rounded-full bg-green-500 mt-2"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{statistics.totalScans} scans stored</p>
                  <p className="text-xs text-muted-foreground">
                    Data retention: {statistics.totalScans > 0 ? 'Active' : 'No data'}
                  </p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}