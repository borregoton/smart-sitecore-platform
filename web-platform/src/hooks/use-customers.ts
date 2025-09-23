import { useState, useEffect } from 'react'
import { CustomerWithSites } from '@/lib/services/customer-service'

export function useCustomers() {
  const [customers, setCustomers] = useState<CustomerWithSites[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchCustomers = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/customers')
      if (!response.ok) {
        throw new Error('Failed to fetch customers')
      }

      const data = await response.json()
      setCustomers(data.customers || [])
    } catch (err) {
      console.error('Error fetching customers:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch customers')
      setCustomers([]) // Reset to empty array on error
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchCustomers()
  }, [])

  return { customers, loading, error, refetch: fetchCustomers }
}

export function useCustomerSites(customerId: string | null) {
  const [sites, setSites] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!customerId) {
      setSites([])
      setLoading(false)
      setError(null)
      return
    }

    async function fetchSites() {
      try {
        setLoading(true)
        setError(null)

        const response = await fetch(`/api/customers/${customerId}/sites`)
        if (!response.ok) {
          throw new Error('Failed to fetch customer sites')
        }

        const data = await response.json()
        setSites(data.sites || [])
      } catch (err) {
        console.error('Error fetching customer sites:', err)
        setError(err instanceof Error ? err.message : 'Failed to fetch sites')
        setSites([])
      } finally {
        setLoading(false)
      }
    }

    fetchSites()
  }, [customerId])

  return { sites, loading, error }
}