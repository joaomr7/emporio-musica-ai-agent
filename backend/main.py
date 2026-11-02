from contextlib import asynccontextmanager

from fastapi import FastAPI
from tortoise.contrib.fastapi import RegisterTortoise

from backend.database import TORTOISE_ORM
from backend.api.sessions import router as sessions_router
from backend.api.customers import router as customers_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with RegisterTortoise(app, config=TORTOISE_ORM):
        yield

app = FastAPI(title='Empório da Música AI Agent', lifespan=lifespan)
app.include_router(sessions_router)
app.include_router(customers_router)