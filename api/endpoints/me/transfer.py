from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import get_current_user
from database.deps import get_session
from database.models import Account, User
from services.transfer import (
    get_user_id, pick_sender_account, resolve_recipient,
    internal_transfer, external_transfer,
)

router = APIRouter(prefix="/me")


@router.post("/transfer")
async def create_transfer(request: Request,
                          user=Depends(get_current_user),
                          db: AsyncSession = Depends(get_session),
                          ):
    data = await request.json()

    recipient_type = data.get("recipient_type")
    recipient_value = data.get("recipient")
    amount = data.get("amount")
    comment = data.get("comment", "")
    from_account_id = data.get("from_account_id")

    if not recipient_type or recipient_value is None or amount is None:
        raise HTTPException(400, "Недостаточно данных для перевода.")

    sender_uid = await get_user_id(db, user["id"])
    sender_acc: Account = await pick_sender_account(db, sender_uid, from_account_id)
    recipient_uid, recipient_acc_row_id, recipient_public_id = await resolve_recipient(db, recipient_type,
                                                                                       recipient_value)

    if sender_acc.account_id == recipient_public_id:
        raise HTTPException(400, "Нельзя перевести на тот же счёт")

    if sender_uid == recipient_uid:
        return await internal_transfer(db, sender_acc, recipient_acc_row_id, sender_uid, amount, comment)

    if sender_acc.balance < amount:
        raise HTTPException(400, "Недостаточно средств")

    code, expires_at = await external_transfer(db, sender_acc, recipient_acc_row_id, sender_uid, amount, comment)

    from sqlalchemy import select
    nick = await db.scalar(
        select(User.nickname)
        .join(Account, Account.owner_id == User.id)
        .where(Account.account_id == recipient_public_id)
    )
    nick = nick or "Неизвестно"

    return {"status": "pending"}
