from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from sqlalchemy.orm import aliased

from api.auth import get_current_user
from database.deps import get_session
from database.models import User, Account, Transaction

router = APIRouter(prefix="/me")

MONTHS_NOMINATIVE = ["", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь", "Июль", "Август", "Сентябрь", "Октябрь",
                     "Ноябрь", "Декабрь"]


@router.get("/summary")
async def get_summary(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    uid = await db.scalar(select(User.id).where(User.tg_id == user["id"]))
    if not uid:
        raise HTTPException(404, "User not found")

    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    sa = aliased(Account)
    ta = aliased(Account)

    q = (
        select(
            Transaction.amount,
            Transaction.created_at,
            sa.owner_id.label("source_owner"),
            ta.owner_id.label("target_owner"),
            func.coalesce(
                select(User.nickname).where(User.id == sa.owner_id).scalar_subquery(),
                "?"
            ).label("from_nick"),
            func.coalesce(
                select(User.nickname).where(User.id == ta.owner_id).scalar_subquery(),
                "?"
            ).label("to_nick"),
        )
        .join(sa, sa.id == Transaction.source_account_id)
        .join(ta, ta.id == Transaction.target_account_id)
        .where(
            ((sa.owner_id == uid) | (ta.owner_id == uid)) &
            (Transaction.created_at >= month_start) &
            (Transaction.status == "confirmed")
        )
        .order_by(Transaction.created_at.desc())
    )

    rows = (await db.execute(q)).all()

    entries, total = [], 0

    def push(sign: int, name: str, date_str: str, amt: int):
        nonlocal total
        total += sign * amt
        entries.append({
            "name": name,
            "amount": sign * amt,
            "type": "Перевод",
            "date": date_str,
        })

    for amount, created_at, source_owner, target_owner, from_nick, to_nick in rows:
        created = created_at.date().isoformat()
        out_user = source_owner == uid
        in_user = target_owner == uid
        internal = out_user and in_user

        if internal:
            continue

        sign = -1 if out_user else 1
        name = to_nick if out_user else from_nick
        push(sign, name, created, amount)

    return {
        "total": total,
        "monthLabel": MONTHS_NOMINATIVE[now.month],
        "entries": list(reversed(entries)),
    }
