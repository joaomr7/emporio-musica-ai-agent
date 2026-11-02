from datetime import timedelta

from tortoise import timezone

from backend.models import ProcessingTask

DEBOUNCE_DELAY = timedelta(seconds=3)

async def schedule_task(session_id: int, connection):
    task = await ProcessingTask.filter(
        session_id=session_id, status='pending'
    ).using_db(connection).first()

    scheduled_at = timezone.now() + DEBOUNCE_DELAY

    if task:
        task.scheduled_at = scheduled_at
        await task.save(using_db=connection, update_fields=['scheduled_at'])
    else:
        task = await ProcessingTask.create(
            session_id=session_id,
            scheduled_at=scheduled_at,
            using_db=connection
        )

    return task