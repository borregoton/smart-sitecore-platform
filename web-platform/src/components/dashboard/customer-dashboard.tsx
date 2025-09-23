'use client'

import { useCustomerContext } from '@/lib/context/customer-context'
import { useCustomerSites } from '@/hooks/use-customers'
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
  Plus
} from 'lucide-react'

export function CustomerDashboard() {
  const { state } = useCustomerContext()
  const { sites, loading: sitesLoading } = useCustomerSites(state.selectedCustomer?.id || null)

  if (!state.selectedCustomer) {
    return (
      <div className="text-center py-12">
        <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
        <h3 className="text-lg font-semibold mb-2">Welcome to Smart Sitecore</h3>
        <p className="text-muted-foreground">
          Select a customer above to view their portfolio dashboard.
        </p>
      </div>
    )
  }

  // Calculate real metrics from sites data
  const totalSites = sites?.length || 0
  const activeSites = sites?.filter(s => s.isActive)?.length || 0
  const avgHealthScore = sites?.length > 0
    ? Math.round(sites.reduce((acc, site) => acc + (site.healthScore || 0), 0) / sites.length)
    : 0
  const recentScans = sites?.filter(s => s.lastScan?.completedAt)?.length || 0
  const lastScanTime = sites?.find(s => s.lastScan?.completedAt)?.lastScan?.completedAt

  return (
    <div className="space-y-6">
      {/* Loading State */}
      {sitesLoading && (
        <div className="text-center py-8">
          <Loader2 className="h-8 w-8 text-muted-foreground mx-auto mb-4 animate-spin" />
          <p className="text-muted-foreground">Loading site data from database...</p>
        </div>
      )}

      {/* Portfolio Overview Cards */}
      {!sitesLoading && (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Sites</CardTitle>
              <Globe className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalSites}</div>
              <p className="text-xs text-muted-foreground">
                {activeSites} active
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Health Score</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {avgHealthScore > 0 ? `${avgHealthScore}%` : 'No data'}
              </div>
              <p className="text-xs text-muted-foreground">
                {recentScans > 0 ? 'From recent scans' : 'Run analysis to get data'}
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
                {lastScanTime ? new Date(lastScanTime).toLocaleDateString() : 'Never'}
              </div>
              <p className="text-xs text-muted-foreground">
                {recentScans} site{recentScans === 1 ? '' : 's'} scanned
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Sites Status</CardTitle>
              <AlertTriangle className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{activeSites}/{totalSites}</div>
              <p className="text-xs text-muted-foreground">
                Sites active and accessible
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Site Grid */}
      {!sitesLoading && (
        <div>
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold">Sites Portfolio ({totalSites})</h3>
            <Button size="sm">
              <Zap className="h-4 w-4 mr-2" />
              Run Analysis
            </Button>
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {sites.map((site) => (
              <Card key={site.id} className="hover:shadow-md transition-shadow">
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between">
                    <CardTitle className="text-base">{site.name}</CardTitle>
                    <Badge
                      variant={site.isActive ? 'default' : 'secondary'}
                      className={site.isActive ? 'status-healthy' : 'status-inactive'}
                    >
                      {site.isActive ? 'Active' : 'Inactive'}
                    </Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div>
                      <p className="text-sm font-medium">{site.fqdn}</p>
                      <p className="text-xs text-muted-foreground">{site.siteType} • {site.environment}</p>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Health Score</span>
                      <div className="flex items-center space-x-1">
                        <div className={`w-2 h-2 rounded-full ${
                          site.healthScore > 80 ? 'bg-green-500' :
                          site.healthScore > 60 ? 'bg-yellow-500' :
                          site.healthScore ? 'bg-red-500' : 'bg-gray-400'
                        }`}></div>
                        <span className="font-medium">
                          {site.healthScore ? `${site.healthScore}%` : 'No data'}
                        </span>
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-sm">
                      <span className="text-muted-foreground">Last Scan</span>
                      <span className="font-medium">
                        {site.lastScan?.completedAt ?
                          new Date(site.lastScan.completedAt).toLocaleDateString() :
                          'Never'}
                      </span>
                    </div>

                    <div className="pt-2 border-t">
                      <Button variant="outline" size="sm" className="w-full">
                        View Details
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* No Sites State */}
          {sites.length === 0 && (
            <div className="text-center py-8 border-2 border-dashed border-muted rounded-lg">
              <Globe className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No Sites Found</h3>
              <p className="text-muted-foreground mb-4">
                This customer doesn't have any sites configured yet.
              </p>
              <Button>
                <Plus className="h-4 w-4 mr-2" />
                Add First Site
              </Button>
            </div>
          )}
        </div>
      )}

      {/* Quick Insights */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <TrendingUp className="h-5 w-5 mr-2" />
              Portfolio Insights
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-blue-50 dark:bg-blue-950 rounded-lg">
              <div>
                <p className="font-medium text-blue-900 dark:text-blue-100">Migration Opportunity</p>
                <p className="text-sm text-blue-700 dark:text-blue-300">3 sites ready for headless migration</p>
              </div>
              <Button variant="outline" size="sm">View</Button>
            </div>

            <div className="flex items-center justify-between p-3 bg-green-50 dark:bg-green-950 rounded-lg">
              <div>
                <p className="font-medium text-green-900 dark:text-green-100">Template Optimization</p>
                <p className="text-sm text-green-700 dark:text-green-300">15% duplication found across sites</p>
              </div>
              <Button variant="outline" size="sm">View</Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="h-5 w-5 mr-2" />
              Recent Activity
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-green-500 mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Analysis completed</p>
                <p className="text-xs text-muted-foreground">www.acme.com • 2 hours ago</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-blue-500 mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Schema updated</p>
                <p className="text-xs text-muted-foreground">api.acme.com • 6 hours ago</p>
              </div>
            </div>

            <div className="flex items-start space-x-3">
              <div className="w-2 h-2 rounded-full bg-yellow-500 mt-2"></div>
              <div className="flex-1">
                <p className="text-sm font-medium">Issue detected</p>
                <p className="text-xs text-muted-foreground">intranet.acme.com • 1 day ago</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}