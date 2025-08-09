from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from database.deps import get_session
from database.models import User

router = APIRouter(prefix="/me")


@router.get("/profile")
async def profile(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    row = await db.execute(select(User.id, User.nickname).where(User.tg_id == user["id"]))
    r = row.first()
    if not r:
        raise HTTPException(404, "User")
    uid, nick = r
    return {
        "nickname": nick,
        "user_id": uid,
        "telegram_id": user["id"],
        "avatar": f"https://mc-heads.net/avatar/{nick}",
    }
