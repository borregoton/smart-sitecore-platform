import './globals.css'
import { Inter } from 'next/font/google'
import { Providers } from '@/components/providers'
import { Toaster } from '@/components/ui/toaster'

const inter = Inter({ subsets: ['latin'] })

export const metadata = {
  title: 'Smart Sitecore Analysis Platform',
  description: 'Enterprise multi-site Sitecore analysis and portfolio management',
  keywords: 'Sitecore, analysis, multi-site, portfolio, migration, GraphQL, content management',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={inter.className}>
        <Providers>
          <div className="min-h-screen bg-background font-sans antialiased">
            <div className="relative flex min-h-screen flex-col">
              <div className="flex-1">
                {children}
              </div>
            </div>
          </div>
          <Toaster />
        </Providers>
      </body>
    </html>
  )
}