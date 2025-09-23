import { Card, CardContent, CardHeader } from "@/components/ui/card"

export function DashboardSkeleton() {
  return (
    <div className="grid gap-6">
      {/* Header Skeleton */}
      <div className="h-8 bg-muted rounded-md animate-pulse" />

      {/* Stats Cards Skeleton */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <div className="h-4 w-20 bg-muted rounded animate-pulse" />
              <div className="h-4 w-4 bg-muted rounded animate-pulse" />
            </CardHeader>
            <CardContent>
              <div className="h-8 w-16 bg-muted rounded animate-pulse mb-2" />
              <div className="h-3 w-24 bg-muted rounded animate-pulse" />
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Main Content Skeleton */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-7">
        <Card className="col-span-4">
          <CardHeader>
            <div className="h-6 w-32 bg-muted rounded animate-pulse" />
          </CardHeader>
          <CardContent className="pl-2">
            <div className="h-48 bg-muted rounded animate-pulse" />
          </CardContent>
        </Card>

        <Card className="col-span-3">
          <CardHeader>
            <div className="h-6 w-28 bg-muted rounded animate-pulse" />
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex items-center space-x-4">
                  <div className="h-8 w-8 bg-muted rounded-full animate-pulse" />
                  <div className="space-y-2 flex-1">
                    <div className="h-4 w-32 bg-muted rounded animate-pulse" />
                    <div className="h-3 w-24 bg-muted rounded animate-pulse" />
                  </div>
                  <div className="h-4 w-12 bg-muted rounded animate-pulse" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}