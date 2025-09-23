'use client'

import { CustomerDashboard } from '@/components/dashboard/customer-dashboard'
import { CustomerSelector } from '@/components/customers/customer-selector'
import { SitecoreDashboard } from '@/components/sitecore/sitecore-dashboard'
import { MainLayout } from '@/components/layout/main-layout'
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs'
import { Suspense, useState } from 'react'
import { DashboardSkeleton } from '@/components/ui/dashboard-skeleton'

export default function HomePage() {
  const [activeTab, setActiveTab] = useState('extracted-data')

  return (
    <MainLayout>
      <div className="flex flex-col space-y-6">
        {/* Header Section */}
        <div className="flex flex-col space-y-2">
          <h1 className="text-3xl font-bold tracking-tight">
            Smart Sitecore Analysis Platform
          </h1>
          <p className="text-muted-foreground">
            Enterprise multi-site Sitecore analysis and portfolio management
          </p>
        </div>

        {/* Navigation Tabs */}
        <Tabs value={activeTab} onValueChange={setActiveTab}>
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="extracted-data">Extracted Sitecore Data</TabsTrigger>
            <TabsTrigger value="customer-portfolio">Customer Portfolio</TabsTrigger>
          </TabsList>

          {/* Extracted Sitecore Data Tab */}
          <TabsContent value="extracted-data">
            <Suspense fallback={<DashboardSkeleton />}>
              <SitecoreDashboard />
            </Suspense>
          </TabsContent>

          {/* Customer Portfolio Tab */}
          <TabsContent value="customer-portfolio">
            {/* Customer Selection */}
            <div className="border-b border-border pb-6 mb-6">
              <Suspense fallback={<div className="h-16 w-full animate-pulse bg-muted rounded" />}>
                <CustomerSelector />
              </Suspense>
            </div>

            {/* Customer Dashboard */}
            <Suspense fallback={<DashboardSkeleton />}>
              <CustomerDashboard />
            </Suspense>
          </TabsContent>
        </Tabs>
      </div>
    </MainLayout>
  )
}