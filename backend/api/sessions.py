
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from tortoise import timezone
from tortoise.transactions import in_transaction

from backend.api.dependencies import get_current_customer, get_session
from backend.api.schemas import MessageCreate, MessageResponse, SessionResponse
from backend.models import Customer, Message, Session
from backend.queue import schedule_task

router = APIRouter(prefix='/sessions', tags=['Sessions'])
SESSION_TIMEOUT = timedelta(hours=24)

@router.post('', response_model=SessionResponse, status_code=200)
async def create_session(customer: Annotated[Customer, Depends(get_current_customer)]):
    now = timezone.now()

    async with in_transaction() as connection:
        await Customer.filter(customer_id=customer.customer_id).using_db(connection).select_for_update().first()

        sessions = await Session.filter(
            customer_id=customer.customer_id,
            status='active'
        ).using_db(connection).order_by('-updated_at')

        active_session = None

        for session in sessions:
            if now - session.updated_at < SESSION_TIMEOUT and active_session is None:
                active_session = session
                continue

            session.status = 'closed'
            session.closed_at = now
            await session.save(using_db=connection, update_fields=['status', 'closed_at'])

        if active_session is None:
            active_session = await Session.create(customer_id=customer.customer_id, using_db=connection)

    return SessionResponse(
        id=active_session.id,
        customer_id=active_session.customer_id,
        status=active_session.status,
        created_at=active_session.created_at
    )

@router.get('/{session_id}', response_model=SessionResponse)
async def read_session(session: Annotated[Session, Depends(get_session)]):
    return SessionResponse(
        id=session.id,
        customer_id=session.customer_id,
        status=session.status,
        created_at=session.created_at
    )

@router.get('/{session_id}/messages', response_model=list[MessageResponse])
async def get_messages(session: Annotated[Session, Depends(get_session)]):
    messages = await Message.filter(session_id=session.id).order_by('created_at', 'id')

    return [
        MessageResponse(
            id=message.id,
            session_id=message.session_id,
            role=message.role,
            content=message.content,
            created_at=message.created_at
        )
        for message in messages
    ]

@router.post('/{session_id}/messages', response_model=MessageResponse, status_code=201)
async def create_message(data: MessageCreate, session: Annotated[Session, Depends(get_session)]):
    async with in_transaction() as connection:
        locked_session = await Session.filter(id=session.id).using_db(connection).select_for_update().first()

        if locked_session is None or locked_session.status != 'active':
            raise HTTPException(status_code=409, detail='Session is not active')

        now = timezone.now()

        if now - locked_session.updated_at >= SESSION_TIMEOUT:
            locked_session.status = 'closed'
            locked_session.closed_at = now
            await locked_session.save(using_db=connection, update_fields=['status', 'closed_at'])
            raise HTTPException(status_code=409, detail='Session has expired')

        message = await Message.create(
            session_id=locked_session.id,
            role='user',
            content=data.content,
            using_db=connection
        )

        locked_session.updated_at = now
        await locked_session.save(using_db=connection, update_fields=['updated_at'])

        # create task
        await schedule_task(locked_session.id, connection)

    return MessageResponse(
        id=message.id,
        session_id=message.session_id,
        role=message.role,
        content=message.content,
        created_at=message.created_at
    )
