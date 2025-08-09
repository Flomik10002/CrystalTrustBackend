from datetime import datetime
from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException

from database.models import User, Account, Transaction


class TransferError(HTTPException):
    pass

async def get_user_id(db: AsyncSession, tg_id: int) -> int:
    uid = await db.scalar(select(User.id).where(User.tg_id == tg_id))
    if not uid:
        raise TransferError(403, "Пользователь не найден")
    return uid

async def pick_sender_account(db: AsyncSession, owner_id: int, from_account_id: int | None) -> Account:
    q = select(Account).where(Account.owner_id == owner_id)
    accounts = list(await db.scalars(q))
    if not accounts:
        raise TransferError(400, "У вас нет ни одного счёта")
    if from_account_id is not None:
        try:
            acc_num = int(str(from_account_id).lstrip('0') or '0')  # "001" → 1
        except ValueError:
            raise TransferError(400, "Неверный формат счёта")

        for a in accounts:
            if a.account_id == acc_num:
                return a
        raise TransferError(403, "Счёт не принадлежит вам")
    return accounts[0]

async def resolve_recipient(db: AsyncSession, recipient_type: str, value: str):
    if recipient_type == "nickname":
        user = await db.scalar(select(User).where(User.nickname == value))
        if not user:
            raise TransferError(404, "Пользователь не найден")
        acc = await db.scalar(select(Account).where(Account.owner_id == user.id, Account.account_type == "personal"))
        if not acc:
            raise TransferError(404, "У пользователя нет счёта")
        return user.id, acc.id, acc.account_id
    if recipient_type == "account":
        clean = value.strip().upper().removeprefix("CRYSTAL-")
        try:
            acc_num = int(clean.lstrip("0") or "0")  # '001' -> 1, '0'->0
        except ValueError:
            raise TransferError(400, "Неверный формат счёта")

        acc = await db.scalar(select(Account).where(Account.account_id == acc_num))
        if not acc:
            raise TransferError(404, "Счёт не найден")

        return acc.owner_id, acc.id, acc.account_id

    raise TransferError(400, "Неверный тип получателя")

async def internal_transfer(db: AsyncSession, src: Account, dst_row_id: int,
                            user_id: int, amount: int, comment: str):
    upd_src = (
        update(Account)
        .where(Account.id == src.id, Account.balance >= amount)
        .values(balance=Account.balance - amount)
        .returning(Account.id)
    )
    if not await db.scalar(upd_src):
        raise TransferError(400, "Недостаточно средств")

    await db.execute(
        update(Account)
        .where(Account.id == dst_row_id)
        .values(balance=Account.balance + amount)
    )

    await db.execute(
        insert(Transaction).values(
            source_account_id=src.id,
            target_account_id=dst_row_id,
            amount=amount,
            status="confirmed",
            initiated_by_user_id=user_id,
            comment=comment,
            confirmed_at=datetime.utcnow()
        )
    )
    await db.commit()
    return {"status": "success", "message": "Перевод между своими счетами выполнен"}

async def external_transfer(db: AsyncSession, src: Account, dst_row_id: int, user_id: int,
                            amount: int, comment: str):
    upd_src = (
        update(Account)
        .where(Account.id == src.id, Account.balance >= amount)
        .values(balance=Account.balance - amount)
        .returning(Account.id)
    )
    if not await db.scalar(upd_src):
        raise TransferError(400, "Недостаточно средств")

    await db.execute(
        update(Account)
        .where(Account.id == dst_row_id)
        .values(balance=Account.balance + amount)
    )

    await db.execute(
        insert(Transaction).values(
            source_account_id=src.id,
            target_account_id=dst_row_id,
            amount=amount,
            status="confirmed",
            initiated_by_user_id=user_id,
            comment=comment,
            confirmed_at=datetime.utcnow()
        )
    )
    await db.commit()
    return None, None
