from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import aliased

from api.auth import get_current_user
from database.deps import get_session
from database.models import User, Account, Transaction

router = APIRouter(prefix="/me")

MONTHS_NOMINATIVE = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]

Moscow_TZ = ZoneInfo("Europe/Moscow")

def to_local(dt_utc: datetime) -> datetime:
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.astimezone(Moscow_TZ)

@router.get("/summary")
async def get_summary(user=Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    uid = await db.scalar(select(User.id).where(User.tg_id == user["id"]))
    if not uid:
        raise HTTPException(404, "User not found")

    now_local = datetime.now(Moscow_TZ)
    month_start_local = datetime(now_local.year, now_local.month, 1, tzinfo=Moscow_TZ)
    month_start_utc_naive = month_start_local.astimezone(timezone.utc).replace(tzinfo=None)

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
            (Transaction.created_at >= month_start_utc_naive) &
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
        created_local = to_local(created_at)
        date_iso = created_local.date().isoformat()

        out_user = source_owner == uid
        in_user = target_owner == uid
        if out_user and in_user:
            continue

        sign = -1 if out_user else 1
        name = to_nick if out_user else from_nick
        push(sign, name, date_iso, amount)

    return {
        "total": total,
        "monthLabel": MONTHS_NOMINATIVE[now_local.month],
        "entries": list(reversed(entries)),  # по возрастанию даты в пределах месяца
    }
