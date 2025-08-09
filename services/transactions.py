from datetime import datetime, timedelta
from typing import Tuple

from sqlalchemy import select, update, func, delete
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from database.models import User, Transaction, Account


async def confirm_transfer(db: AsyncSession, code: str, tg_id: int) -> Tuple[bool, str]:
    """Подтверждение pending-перевода.
    Возвращает (ok, msg).
    """
    uid = await db.scalar(select(User.id).where(User.tg_id == tg_id))
    if not uid:
        return False, "Вы не зарегистрированы."

    tx = await db.scalar(
        select(Transaction)
        .where(
            Transaction.confirmation_code == code,
            Transaction.status == 'pending',
            Transaction.expires_at > datetime.utcnow(),
            Transaction.initiated_by_user_id == uid,
        )
    )
    if not tx:
        return False, "Код не найден / устарел / не ваш."

    src = await db.scalar(select(Account).where(Account.id == tx.source_account_id))
    dst = await db.scalar(select(Account).where(Account.id == tx.target_account_id))
    if not src or not dst:
        return False, "Счёт не найден."

    upd_src = (
        update(Account)
        .where(Account.id == src.id, Account.balance >= tx.amount)
        .values(balance=Account.balance - tx.amount)
        .returning(Account.id)
    )
    if not await db.scalar(upd_src):
        return False, "Недостаточно средств."

    await db.execute(
        update(Account)
        .where(Account.id == dst.id)
        .values(balance=Account.balance + tx.amount)
    )

    tx.status = 'confirmed'
    tx.confirmed_at = datetime.utcnow()
    await db.flush()
    await db.commit()
    return True, f"✅ Перевод на {tx.amount} АР подтверждён."

async def cancel_transfer(db: AsyncSession, code: str, tg_id: int) -> Tuple[bool, str]:
    uid = await db.scalar(select(User.id).where(User.tg_id == tg_id))
    if not uid:
        return False, "Вы не зарегистрированы."

    tx = await db.scalar(
        select(Transaction)
        .where(
            Transaction.confirmation_code == code,
            Transaction.status == 'pending',
            Transaction.expires_at > func.now(),
            Transaction.initiated_by_user_id == uid,
        )
    )
    if not tx:
        return False, "Ничего не найдено или уже подтверждено/отменено."

    async with db.begin():
        tx.status = 'cancelled'
        await db.flush()
    return True, "❌ Перевод отменён."


async def cleanup_expired(db: AsyncSession) -> int:
    """Удалить истёкшие pending-транзакции. Возвращает кол-во удалённых."""
    res = await db.execute(
        delete(Transaction).where(Transaction.status == 'pending', Transaction.expires_at < func.now())
    )
    await db.commit()
    return res.rowcount or 0
