'use client'

import { ReactNode } from 'react'
import { Navigation } from './navigation'
import { Header } from './header'
import { useCustomerContext } from '@/lib/context/customer-context'
import { cn } from '@/lib/utils'

interface MainLayoutProps {
  children: ReactNode
  className?: string
}

export function MainLayout({ children, className }: MainLayoutProps) {
  const { state } = useCustomerContext()

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <Header />

      <div className="flex">
        {/* Sidebar Navigation */}
        <Navigation />

        {/* Main Content */}
        <main className={cn(
          "flex-1 p-6",
          "ml-64", // Account for fixed sidebar width
          className
        )}>
          {/* Customer Context Banner */}
          {state.selectedCustomer && (
            <div className="mb-6 rounded-lg border border-sitecore-200 bg-sitecore-50 p-4 dark:border-sitecore-800 dark:bg-sitecore-950">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sitecore-100 dark:bg-sitecore-900">
                    <span className="text-sm font-semibold text-sitecore-700 dark:text-sitecore-300">
                      {state.selectedCustomer.customerCode}
                    </span>
                  </div>
                  <div>
                    <h2 className="font-semibold text-sitecore-900 dark:text-sitecore-100">
                      {state.selectedCustomer.displayName}
                    </h2>
                    <p className="text-sm text-sitecore-600 dark:text-sitecore-400">
                      {state.selectedSites.length > 0
                        ? `${state.selectedSites.length} site${state.selectedSites.length === 1 ? '' : 's'} selected`
                        : 'Portfolio analysis mode'
                      }
                    </p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  <div className={cn(
                    "status-indicator",
                    state.analysisScope === 'single' && "status-healthy",
                    state.analysisScope === 'portfolio' && "bg-blue-50 text-blue-700 dark:bg-blue-500/10 dark:text-blue-400",
                    state.analysisScope === 'comparison' && "bg-purple-50 text-purple-700 dark:bg-purple-500/10 dark:text-purple-400"
                  )}>
                    {state.analysisScope === 'single' && 'Single Site'}
                    {state.analysisScope === 'portfolio' && 'Portfolio View'}
                    {state.analysisScope === 'comparison' && 'Site Comparison'}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Error Banner */}
          {state.error && (
            <div className="mb-6 rounded-lg border border-red-200 bg-red-50 p-4 dark:border-red-800 dark:bg-red-950">
              <div className="flex items-center space-x-2">
                <div className="text-red-600 dark:text-red-400">
                  <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div>
                  <h3 className="font-medium text-red-800 dark:text-red-200">
                    Error
                  </h3>
                  <p className="text-sm text-red-600 dark:text-red-400">
                    {state.error}
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Main Content */}
          <div className="animate-fade-in">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}