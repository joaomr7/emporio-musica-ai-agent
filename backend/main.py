from contextlib import asynccontextmanager
from fastapi import FastAPI
from backend.database import close_db, init_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    try:
        yield
    finally:
        await close_db()

app = FastAPI(title='Empório da Música AI Agent', lifespan=lifespan)

@app.get('/test')
async def test():
    return {'status': 'ok'}