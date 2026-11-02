from fastapi import APIRouter

from backend.models import Customer

router = APIRouter(prefix='/customers', tags=['Customers'])

@router.get('')
async def list_customers():
    customers = await Customer.all().order_by('name')

    return [
        {
            'customer_id': customer.customer_id,
            'name': customer.name
        }
        for customer in customers
    ]