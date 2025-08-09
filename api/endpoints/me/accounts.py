from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from database.deps import get_session
from database.models import Account, Business, User

router = APIRouter(prefix="/me")


@router.get("/accounts")
async def get_accounts(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    uid = await db.scalar(select(User.id).where(User.tg_id == user["id"]))
    if not uid:
        raise HTTPException(404, "Пользователь не найден")

    q = (
        select(
            Account.account_id,
            Account.account_type,
            Account.balance,
            Business.name,
            Business.tag,
            Business.category,
        )
        .join(Business, Business.account_id == Account.id, isouter=True)
        .where(Account.owner_id == uid)
    )
    rows = (await db.execute(q)).all()

    out = []
    for acc_id, acc_type, bal, b_name, b_tag, b_cat in rows:
        is_business = acc_type == "business"
        out.append({
            "id": acc_id,
            "type": acc_type,
            "balance": bal,
            "business": {
                "name": b_name,
                "tag": b_tag,
                "category": b_cat,
            } if is_business else None,
        })
    return {"accounts": out}
