from tortoise import Tortoise
from backend.config import settings

TORTOISE_ORM = {
    'connections': {
        'default': settings.database_url,
    },
    'apps': {
        'models': {
            'models': ['backend.models'],
            'default_connection': 'default',
            'migrations': 'backend.migrations',
        },
    }
}

async def init_db():
    await Tortoise.init(config=TORTOISE_ORM)

async def close_db():
    await Tortoise.close_connections()