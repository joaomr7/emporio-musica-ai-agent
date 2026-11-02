import asyncio

from tortoise import timezone
from tortoise.transactions import in_transaction

from backend.database import close_db, init_db
from backend.models import Message, ProcessingTask

POLL_INTERVAL = 1

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
            task_id=None
        ).using_db(connection).order_by('created_at', 'id')

        if not messages:
            task.status = 'failed'
            task.error = 'No messages available for processing'
            await task.save(using_db=connection)
            return None

        await Message.filter(id__in=[message.id for message in messages]).using_db(connection).update(task_id=task.id)

        task.status = 'processing'
        task.started_at = timezone.now()
        task.attempts += 1
        await task.save(using_db=connection)

        return task.id, task.session_id, [message.content for message in messages]

async def process_messages(messages: list[str]) -> str:
    return f'Recebi suas mensagens: {" | ".join(messages)}'

async def execute_task(task_id: int, session_id: int, messages: list[str]):
    try:
        response = await process_messages(messages)

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
        await ProcessingTask.filter(id=task_id).update(
            status='failed',
            error=str(exc)
        )
        raise

async def run_worker():
    await init_db()

    try:
        while True:
            reserved = await reserve_task()

            if reserved is not None:
                task_id, session_id, messages = reserved

                try:
                    await execute_task(task_id, session_id, messages)
                    print(f'Task {task_id} completed')
                except Exception as exc:
                    print(f'Task {task_id} failed: {exc}')
            else:
                await asyncio.sleep(POLL_INTERVAL)

    finally:
        await close_db()

if __name__ == '__main__':
    try:
        asyncio.run(run_worker())
    except KeyboardInterrupt:
        print('Worker stopped')
