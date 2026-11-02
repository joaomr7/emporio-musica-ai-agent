import asyncio
from uuid import uuid4

from httpx import ASGITransport, AsyncClient

from backend.config import settings
from backend.database import close_db, init_db
from backend.main import app
from backend.models import Customer, Message, ProcessingTask, Session

async def check_message_tasks():
    assert settings.database_url.rsplit('/', 1)[-1] == 'emporio_test', 'Use the test database'

    await init_db()
    customer = None

    try:
        customer = await Customer.create(
            name='Test Customer',
            phone='00000000000',
            email=f'{uuid4().hex}@example.com',
            city='Test City'
        )

        headers = {'X-Customer-ID': str(customer.customer_id)}
        transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url='http://test') as client:
            response = await client.post('/sessions', headers=headers)
            assert response.status_code == 200, response.text

            session_id = response.json()['id']

            response = await client.post(
                f'/sessions/{session_id}/messages',
                headers=headers,
                json={'content': 'Olá, gostaria de um violão'}
            )
            assert response.status_code == 201, response.text

            task = await ProcessingTask.get(session_id=session_id)
            task_id = task.id
            first_schedule = task.scheduled_at

            response = await client.post(
                f'/sessions/{session_id}/messages',
                headers=headers,
                json={'content': 'Até R$ 1000'}
            )
            assert response.status_code == 201, response.text

            tasks = await ProcessingTask.filter(session_id=session_id)
            messages = await Message.filter(session_id=session_id).order_by('id')

            assert len(tasks) == 1
            assert tasks[0].id == task_id
            assert tasks[0].status == 'pending'
            assert tasks[0].scheduled_at >= first_schedule

            assert len(messages) == 2
            assert messages[0].content == 'Olá, gostaria de um violão'
            assert messages[1].content == 'Até R$ 1000'

            print('Message and task integration test passed')

    finally:
        if customer is not None:
            sessions = await Session.filter(customer_id=customer.customer_id).values_list('id', flat=True)

            await Message.filter(session_id__in=sessions).delete()
            await ProcessingTask.filter(session_id__in=sessions).delete()
            await Session.filter(id__in=sessions).delete()
            await customer.delete()

        await close_db()

def test_message_tasks():
    asyncio.run(check_message_tasks())
