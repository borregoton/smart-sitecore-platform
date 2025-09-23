'use client'

import { Button } from '@/components/ui/button'
import { ModeToggle } from '@/components/ui/mode-toggle'
import { User } from 'lucide-react'

export function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center px-6">
        {/* Logo */}
        <div className="mr-4 flex items-center space-x-2">
          <div className="h-8 w-8 rounded bg-gradient-sitecore flex items-center justify-center">
            <span className="text-sm font-bold text-white">S</span>
          </div>
          <span className="hidden font-bold sm:inline-block">
            Smart Sitecore
          </span>
        </div>

        {/* Spacer */}
        <div className="flex flex-1" />

        {/* Right side */}
        <div className="flex items-center space-x-2">
          <ModeToggle />
          <Button variant="ghost" size="sm">
            <User className="h-4 w-4" />
            <span className="sr-only">User menu</span>
          </Button>
        </div>
      </div>
    </header>
  )
}