import asyncio

from datetime import timedelta

from tortoise import timezone
from tortoise.transactions import in_transaction

from backend.agent.service import process_conversation
from backend.database import close_db, init_db
from backend.models import Message, ProcessingTask

POLL_INTERVAL = 1
MAX_ATTEMPTS = 3
RETRY_DELAY = 10
TASK_TIMEOUT = 300

async def recover_tasks(startup: bool = False):
    now = timezone.now()
    expired_at = now - timedelta(seconds=TASK_TIMEOUT)

    async with in_transaction() as connection:
        tasks = await ProcessingTask.filter(
            status__in=['processing', 'failed'],
            attempts__lt=MAX_ATTEMPTS
        ).using_db(connection).select_for_update(skip_locked=True)

        recovered = 0

        for task in tasks:
            if task.status == 'processing' and not startup:
                if task.started_at is not None and task.started_at > expired_at:
                    continue

            task.status = 'pending'
            task.scheduled_at = now
            task.started_at = None
            task.completed_at = None
            task.error = None
            await task.save(using_db=connection)

            recovered += 1

    return recovered

async def reserve_task():
    async with in_transaction() as connection:
        task = await ProcessingTask.filter(
            status='pending',
            scheduled_at__lte=timezone.now()
        ).using_db(connection).select_for_update(
            skip_locked=True
        ).order_by('scheduled_at', 'id').first()

        if task is None:
            return None

        messages = await Message.filter(
            session_id=task.session_id,
            role='user',
            task_id=task.id
        ).using_db(connection).order_by('created_at', 'id')

        if not messages and task.attempts == 0:
            messages = await Message.filter(
                session_id=task.session_id,
                role='user',
                task_id=None
            ).using_db(connection).order_by('created_at', 'id')

            if messages:
                await Message.filter(
                    id__in=[message.id for message in messages]
                ).using_db(connection).update(task_id=task.id)

        if not messages:
            task.status = 'failed'
            task.error = 'No messages available for processing'
            await task.save(using_db=connection)
            return None

        if task.attempts >= MAX_ATTEMPTS:
            task.status = 'failed'
            task.error = 'Maximum attempts reached'
            await task.save(using_db=connection)
            return None

        task.status = 'processing'
        task.started_at = timezone.now()
        task.attempts += 1
        await task.save(using_db=connection)

        return task.id, task.session_id, [message.content for message in messages]

async def execute_task(task_id: int, session_id: int):
    try:
        response = await process_conversation(session_id, task_id)

        async with in_transaction() as connection:
            await Message.create(
                session_id=session_id,
                task_id=task_id,
                role='assistant',
                content=response,
                using_db=connection
            )

            await ProcessingTask.filter(id=task_id).using_db(connection).update(
                status='completed',
                completed_at=timezone.now(),
                error=None
            )

    except Exception as exc:
        async with in_transaction() as connection:
            task = await ProcessingTask.filter(id=task_id).using_db(
                connection
            ).select_for_update().first()

            if task is not None:
                task.error = str(exc)
                task.started_at = None

                if task.attempts < MAX_ATTEMPTS:
                    task.status = 'pending'
                    task.scheduled_at = timezone.now() + timedelta(seconds=RETRY_DELAY)
                else:
                    task.status = 'failed'

                await task.save(using_db=connection)

        raise

async def run_worker():
    await init_db()

    try:
        recovered = await recover_tasks(startup=True)

        if recovered:
            print(f'Recovered {recovered} tasks')

        while True:
            await recover_tasks()
            reserved = await reserve_task()

            if reserved is not None:
                task_id, session_id, _ = reserved

                try:
                    await execute_task(task_id, session_id)
                    print(f'Task {task_id} completed')
                except Exception as exc:
                    print(f'Task {task_id} execution failed: {exc}')
            else:
                await asyncio.sleep(POLL_INTERVAL)

    finally:
        await close_db()

if __name__ == '__main__':
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print('Worker stopped')
