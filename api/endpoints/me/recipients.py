from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from api.auth import get_current_user
from database.deps import get_session
from database.models import Transaction, Account, User
from settings import a_settings

router = APIRouter(prefix="/me")


@router.get("/recent-recipients")
async def recent_recipients(
        user=Depends(get_current_user),
        db: AsyncSession = Depends(get_session)
):
    cur_user = await db.scalar(
        select(User).where(User.tg_id == user["id"])
    )
    if not cur_user:
        raise HTTPException(404, "User not found")

    uid = cur_user.id
    my_nick = cur_user.nickname

    sender_acc_ids = list(
        await db.scalars(select(Account.id).where(Account.owner_id == uid))
    )
    if not sender_acc_ids:
        return []

    q = (
        select(User.nickname)
        .join(Account, Account.owner_id == User.id)
        .join(Transaction, Transaction.target_account_id == Account.id)
        .where(Transaction.source_account_id.in_(sender_acc_ids))
        .where(User.id != uid)
        .where(User.nickname != a_settings.BANK_NICK)
        .order_by(Transaction.created_at.desc())
        .limit(50)
    )
    rows = (await db.execute(q)).scalars().all()

    seen, out = set(), []
    for nick in rows:
        if nick == my_nick:
            continue
        if nick not in seen:
            seen.add(nick)
            out.append({
                "nickname": nick,
                "avatar": f"https://mc-heads.net/avatar/{nick}"
            })
        if len(out) == 4:
            break
    return out
