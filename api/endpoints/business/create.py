import re
from fastapi import APIRouter, Depends, HTTPException, Body, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from database.deps import get_session
from database.models import Business, Account
from services.account import generate_account_id
from services.user import get_user_by_tg

router = APIRouter(prefix="/business")

ALLOWED_CATEGORIES = {"build", "industrial", "store", "casino", "entertainment", "other"}
TAG_RE = re.compile(r"^[a-z0-9_-]{3,20}$")

@router.post("/create-business", status_code=status.HTTP_201_CREATED)
async def create_business_account(payload: dict = Body(...),
                                  user=Depends(get_current_user),
                                  db: AsyncSession = Depends(get_session)):
    name = (payload.get("name") or "").strip()
    tag = (payload.get("tag") or "").strip().lower()
    category = payload.get("category")

    if not (name and tag and category):
        raise HTTPException(400, "Нужны поля name, tag, category")
    if category not in ALLOWED_CATEGORIES:
        raise HTTPException(400, f"Неверная категория. Допустимые: {', '.join(ALLOWED_CATEGORIES)}")
    if not TAG_RE.fullmatch(tag):
        raise HTTPException(400, "Tag должен быть 3-20 символов: a-z, 0-9, '_', '-' ")

    db_user = await get_user_by_tg(db, user["id"])
    if not db_user:
        raise HTTPException(403, "Пользователь не найден")

    exists = await db.scalar(select(Business.id).where(Business.tag == tag))
    if exists:
        raise HTTPException(409, "Такой tag уже занят")

    try:
        new_public_account_id = await generate_account_id(db, "business")
        acc = Account(account_id=new_public_account_id, owner_id=db_user.id, balance=0, account_type="business")
        db.add(acc)
        await db.flush()

        biz = Business(account_id=acc.id, owner_id=db_user.id, name=name, tag=tag, category=category)
        db.add(biz)

        await db.commit()

        return {"status": "success", "account_id": new_public_account_id, "tag": tag}
    except Exception as e:
        await db.rollback()
        raise HTTPException(500, detail=f"Ошибка при создании бизнеса: {e}")