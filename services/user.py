from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User


async def get_user_by_tg(db: AsyncSession, tg_id: int) -> User | None:
    return await db.scalar(select(User).where(User.tg_id == tg_id))