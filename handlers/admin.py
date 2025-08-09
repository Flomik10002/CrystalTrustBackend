from datetime import datetime

from aiogram import Router, types
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import SessionLocal
from database.models import Transaction, Account, User
from utils import is_admin

router = Router()


async def get_user_account(db, nickname: str):
    user = await db.scalar(select(User).where(User.nickname == nickname))
    if not user:
        return None, None
    acc = await db.scalar(select(Account).where(Account.owner_id == user.id))
    return user, acc

async def get_bank_account(db):
    bank_user = await db.scalar(select(User).where(User.tg_id == 0))
    if not bank_user:
        raise Exception("CrystalBank не найден!")

    bank_account = await db.scalar(select(Account).where(Account.owner_id == bank_user.id))
    if not bank_account:
        raise Exception("У CrystalBank нет аккаунта!")

    return bank_account

async def get_initiating_user(db, tg_id: int):
    return await db.scalar(select(User).where(User.tg_id == tg_id))

@router.message(Command("deposit"))
async def deposit_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Нет доступа")

    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("⚠️ Использование: /deposit <ник> <сумма>")

    nickname, amount_str = parts[1], parts[2]
    if not amount_str.isdigit() or int(amount_str) <= 0:
        return await message.answer("⚠️ Сумма должна быть положительным числом")

    amount = int(amount_str)

    async with SessionLocal() as db:
        user, acc = await get_user_account(db, nickname)
        if not user:
            return await message.answer("❌ Пользователь не найден")
        if not acc:
            return await message.answer("❌ У пользователя нет счёта")

        initiating_user = await get_initiating_user(db, message.from_user.id)
        if not initiating_user:
            return await message.answer("⚠️ Вы не зарегистрированы в системе")

        bank_acc = await get_bank_account(db)

        acc.balance += amount
        tx = Transaction(
            source_account_id=bank_acc.id,
            target_account_id=acc.id,
            amount=amount,
            status="confirmed",
            initiated_by_user_id=initiating_user.id,
            comment="Пополнение в банке",
            confirmed_at=datetime.utcnow(),
        )
        db.add(tx)
        await db.commit()

        await message.answer(f"✅ {amount} АР начислено игроку {nickname}")

@router.message(Command("withdraw"))
async def withdraw_handler(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("⛔ Нет доступа")

    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("⚠️ Использование: /withdraw <ник> <сумма>")

    nickname, amount_str = parts[1], parts[2]
    if not amount_str.isdigit() or int(amount_str) <= 0:
        return await message.answer("⚠️ Сумма должна быть положительным числом")

    amount = int(amount_str)

    async with SessionLocal() as db:
        user, acc = await get_user_account(db, nickname)
        if not user:
            return await message.answer("❌ Пользователь не найден")
        if not acc:
            return await message.answer("❌ У пользователя нет счёта")
        if acc.balance < amount:
            return await message.answer("❌ Недостаточно средств на счёте")

        initiating_user = await get_initiating_user(db, message.from_user.id)
        if not initiating_user:
            return await message.answer("⚠️ Вы не зарегистрированы в системе")

        bank_acc = await get_bank_account(db)

        acc.balance -= amount
        tx = Transaction(
            source_account_id=acc.id,
            target_account_id=bank_acc.id,
            amount=amount,
            status="confirmed",
            initiated_by_user_id=initiating_user.id,
            comment="Снятие в банке",
            confirmed_at=datetime.utcnow(),
        )
        db.add(tx)
        await db.commit()

        await message.answer(f"{amount} АР снято со счёта {nickname}")
