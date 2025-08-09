from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from database.deps import get_session


async def deps(user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    return user, db