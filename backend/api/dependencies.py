from datetime import timedelta
from typing import Annotated

from fastapi import Depends, Header, HTTPException
from tortoise import timezone

from backend.models import Customer, Session

SESSION_TIMEOUT = timedelta(hours=24)

async def get_current_customer(x_customer_id: Annotated[int, Header()]):
    customer = await Customer.get_or_none(customer_id=x_customer_id)

    if customer is None:
        raise HTTPException(status_code=401, detail='Invalid customer')

    return customer

async def get_session(session_id: int, customer: Annotated[Customer, Depends(get_current_customer)]):
    session = await Session.get_or_none(id=session_id, customer_id=customer.customer_id)

    if session is None:
        raise HTTPException(status_code=404, detail='Session not found')

    if session.status == 'active' and timezone.now() - session.updated_at >= SESSION_TIMEOUT:
        session.status = 'closed'
        session.closed_at = timezone.now()
        await session.save(update_fields=['status', 'closed_at'])

    return session