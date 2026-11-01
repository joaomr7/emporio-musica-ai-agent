from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend.database import close_db, init_db
from backend.api.sessions import router as sessions_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        yield
    finally:
        await close_db()

app = FastAPI(title='Empório da Música AI Agent', lifespan=lifespan)
app.include_router(sessions_router)