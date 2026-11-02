from datetime import timedelta

from tortoise import timezone

from backend.models import ProcessingTask

DEBOUNCE_DELAY = timedelta(seconds=3)
MAX_WAIT = timedelta(seconds=10)

async def schedule_task(session_id: int, connection):
    now = timezone.now()

    task = await ProcessingTask.filter(
        session_id=session_id, status='pending'
    ).using_db(connection).first()

    if task:
        task.scheduled_at = min(now + DEBOUNCE_DELAY, task.created_at + MAX_WAIT)
        await task.save(using_db=connection, update_fields=['scheduled_at'])
    else:
        task = await ProcessingTask.create(
            session_id=session_id,
            scheduled_at=now + DEBOUNCE_DELAY,
            using_db=connection
        )

    return task