from typing import AsyncGenerator
from database.engine import SessionLocal

async def get_session() -> AsyncGenerator:
    async with SessionLocal() as session:
        yield session