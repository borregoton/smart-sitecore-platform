'use client'

import { useState, useEffect } from 'react'
import { useCustomerContext } from '@/lib/context/customer-context'
import { useCustomers } from '@/hooks/use-customers'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Building2, Globe, Plus, Loader2, AlertCircle } from 'lucide-react'

export function CustomerSelector() {
  const { state, setCustomer, setSites } = useCustomerContext()
  const { customers, loading, error } = useCustomers()
  const [showCreateCustomer, setShowCreateCustomer] = useState(false)

  const handleCustomerSelect = (customer: any) => {
    setCustomer(customer)
    setSites(customer.sites || [])
  }

  return (
    <div className="space-y-4">
      {/* Current Selection Display */}
      {state.selectedCustomer ? (
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-full bg-sitecore-100 dark:bg-sitecore-900">
              <Building2 className="h-5 w-5 text-sitecore-600 dark:text-sitecore-400" />
            </div>
            <div>
              <h3 className="font-semibold">
                {state.selectedCustomer.displayName}
              </h3>
              <p className="text-sm text-muted-foreground">
                {state.selectedSites.length} site{state.selectedSites.length === 1 ? '' : 's'} available
              </p>
            </div>
          </div>
          <Button
            variant="outline"
            onClick={() => {
              setCustomer(null)
              setSites([])
            }}
          >
            Change Customer
          </Button>
        </div>
      ) : (
        <>
          {/* Loading State */}
          {loading && (
            <div className="text-center py-12">
              <Loader2 className="h-8 w-8 text-muted-foreground mx-auto mb-4 animate-spin" />
              <h3 className="text-lg font-semibold mb-2">Loading Customers</h3>
              <p className="text-muted-foreground">
                Fetching your Sitecore customers from the database...
              </p>
            </div>
          )}

          {/* Error State */}
          {error && !loading && (
            <div className="text-center py-12">
              <AlertCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2 text-red-600">Connection Error</h3>
              <p className="text-muted-foreground mb-4">
                Unable to connect to the database at 10.0.0.919
              </p>
              <p className="text-sm text-muted-foreground mb-4">
                {error}
              </p>
              <Button
                variant="outline"
                onClick={() => window.location.reload()}
              >
                Retry Connection
              </Button>
            </div>
          )}

          {/* Customer Selection Grid */}
          {!loading && !error && (
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold">Select Customer</h2>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowCreateCustomer(true)}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  Add Customer
                </Button>
              </div>

              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                {customers.map((customer) => (
                  <Card
                    key={customer.id}
                    className="cursor-pointer transition-all hover:shadow-md hover:border-sitecore-300 dark:hover:border-sitecore-700"
                    onClick={() => handleCustomerSelect(customer)}
                  >
                    <CardHeader className="pb-3">
                      <div className="flex items-center justify-between">
                        <CardTitle className="text-base">
                          {customer.displayName}
                        </CardTitle>
                        <Badge variant={customer.isActive ? 'default' : 'secondary'}>
                          {customer.subscriptionTier}
                        </Badge>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-2">
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Building2 className="h-4 w-4 mr-2" />
                          {customer.industry} • {customer.companySize}
                        </div>
                        <div className="flex items-center text-sm text-muted-foreground">
                          <Globe className="h-4 w-4 mr-2" />
                          {customer.sites?.length || 0} site{(customer.sites?.length || 0) === 1 ? '' : 's'}
                        </div>
                        {customer.domain && (
                          <div className="text-sm text-muted-foreground">
                            {customer.domain}
                          </div>
                        )}
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </div>
          )}

          {/* Empty State */}
          {!loading && !error && customers.length === 0 && (
            <div className="text-center py-12">
              <Building2 className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <h3 className="text-lg font-semibold mb-2">No customers found</h3>
              <p className="text-muted-foreground mb-4">
                The database is connected but no customers exist yet.
              </p>
              <Button onClick={() => setShowCreateCustomer(true)}>
                <Plus className="h-4 w-4 mr-2" />
                Add Your First Customer
              </Button>
            </div>
          )}
        </>
      )}
    </div>
  )
}