import { NextResponse } from 'next/server'
import { CustomerService } from '@/lib/services/customer-service'

export async function GET() {
  try {
    const customers = await CustomerService.getAllCustomers()
    return NextResponse.json({ customers })
  } catch (error) {
    console.error('API Error - GET /api/customers:', error)
    return NextResponse.json(
      { error: 'Failed to fetch customers' },
      { status: 500 }
    )
  }
}