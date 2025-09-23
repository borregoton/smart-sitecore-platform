import { NextResponse } from 'next/server'
import { CustomerService } from '@/lib/services/customer-service'

export async function GET(
  request: Request,
  { params }: { params: { customerId: string } }
) {
  try {
    const customer = await CustomerService.getCustomerById(params.customerId)

    if (!customer) {
      return NextResponse.json(
        { error: 'Customer not found' },
        { status: 404 }
      )
    }

    return NextResponse.json({ customer })
  } catch (error) {
    console.error('API Error - GET /api/customers/[customerId]:', error)
    return NextResponse.json(
      { error: 'Failed to fetch customer' },
      { status: 500 }
    )
  }
}