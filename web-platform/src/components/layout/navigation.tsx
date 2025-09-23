'use client'

import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import {
  Building2,
  BarChart3,
  GitCompare,
  Target,
  Settings,
  Zap,
  Globe,
} from 'lucide-react'

const navigation = [
  {
    name: 'Portfolio',
    href: '/',
    icon: Building2,
    description: 'Customer portfolio overview',
  },
  {
    name: 'Sites',
    href: '/sites',
    icon: Globe,
    description: 'Manage customer sites',
  },
  {
    name: 'Analysis',
    href: '/analysis',
    icon: BarChart3,
    description: 'Run and view analysis',
  },
  {
    name: 'Compare',
    href: '/compare',
    icon: GitCompare,
    description: 'Cross-site comparison',
  },
  {
    name: 'Benchmark',
    href: '/benchmark',
    icon: Target,
    description: 'Industry benchmarks',
  },
  {
    name: 'Insights',
    href: '/insights',
    icon: Zap,
    description: 'AI-powered insights',
  },
]

const secondaryNavigation = [
  {
    name: 'Settings',
    href: '/settings',
    icon: Settings,
  },
]

export function Navigation() {
  const pathname = usePathname()

  return (
    <nav className="fixed left-0 top-14 z-40 h-[calc(100vh-3.5rem)] w-64 border-r bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="flex h-full flex-col">
        {/* Main Navigation */}
        <div className="flex-1 space-y-1 p-4">
          <div className="space-y-1">
            {navigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-sitecore-100 text-sitecore-900 dark:bg-sitecore-900 dark:text-sitecore-100'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <item.icon
                    className={cn(
                      'mr-3 h-5 w-5 transition-colors',
                      isActive
                        ? 'text-sitecore-600 dark:text-sitecore-400'
                        : 'text-muted-foreground group-hover:text-accent-foreground'
                    )}
                  />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>
        </div>

        {/* Secondary Navigation */}
        <div className="border-t p-4">
          <div className="space-y-1">
            {secondaryNavigation.map((item) => {
              const isActive = pathname === item.href
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    'group flex items-center rounded-md px-3 py-2 text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-accent text-accent-foreground'
                      : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
                  )}
                >
                  <item.icon className="mr-3 h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              )
            })}
          </div>
        </div>
      </div>
    </nav>
  )
}