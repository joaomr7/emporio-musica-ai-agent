import asyncio

from tortoise import timezone
from tortoise.transactions import in_transaction

from backend.config import settings
from backend.database import close_db, init_db
from backend.models import Customer, Message, ProcessingTask, Session
from backend.queue import schedule_task
from backend.worker import execute_task, reserve_task

async def check_worker():
    assert settings.database_url.rsplit('/', 1)[-1] == 'emporio_test', 'Use the test database'

    await init_db()
    customer = None

    try:
        customer = await Customer.create(
            name='Worker Test',
            phone='00000000000',
            email='worker-test@example.com',
            city='Test City'
        )
        session = await Session.create(customer=customer)

        async with in_transaction() as connection:
            await Message.create(session=session, role='user', content='Quero um violão', using_db=connection)
            await Message.create(session=session, role='user', content='Até R$ 1000', using_db=connection)
            task = await schedule_task(session.id, connection)

        # task can't be reserved until it's schedule time
        assert await reserve_task() is None

        # update shedule to now
        task.scheduled_at = timezone.now()
        await task.save(update_fields=['scheduled_at'])

        reserved = await reserve_task()

        assert reserved is not None
        task_id, session_id, messages = reserved

        assert task_id == task.id
        assert session_id == session.id
        assert messages == ['Quero um violão', 'Até R$ 1000']

        task = await ProcessingTask.get(id=task_id)
        assert task.status == 'processing'
        assert task.attempts == 1

        # same task can't be reserved again
        assert await reserve_task() is None

        await execute_task(task_id, session_id, messages)

        task = await ProcessingTask.get(id=task_id)
        assert task.status == 'completed'
        assert task.completed_at is not None

        saved_messages = await Message.filter(session_id=session.id).order_by('id')

        assert len(saved_messages) == 3
        assert [message.role for message in saved_messages] == ['user', 'user', 'assistant']
        assert saved_messages[2].content == 'Recebi suas mensagens: Quero um violão | Até R$ 1000'
        assert all(message.task_id == task_id for message in saved_messages)

    finally:
        if customer is not None:
            sessions = await Session.filter(customer_id=customer.customer_id).values_list('id', flat=True)
            await Message.filter(session_id__in=sessions).delete()
            await ProcessingTask.filter(session_id__in=sessions).delete()
            await Session.filter(id__in=sessions).delete()
            await customer.delete()

        await close_db()

def test_worker():
    asyncio.run(check_worker())
