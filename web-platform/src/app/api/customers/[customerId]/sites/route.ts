import { NextResponse } from 'next/server'
import { CustomerService } from '@/lib/services/customer-service'

export async function GET(
  request: Request,
  { params }: { params: { customerId: string } }
) {
  try {
    const sites = await CustomerService.getCustomerSitesWithStats(params.customerId)
    return NextResponse.json({ sites })
  } catch (error) {
    console.error('API Error - GET /api/customers/[customerId]/sites:', error)
    return NextResponse.json(
      { error: 'Failed to fetch customer sites' },
      { status: 500 }
    )
  }
}