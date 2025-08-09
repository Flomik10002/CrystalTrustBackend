import re
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from sqlalchemy import select

from database.engine import SessionLocal
from database.models import User
from services.registration import (
    insert_pending_registration,
    verify_registration_code,
    complete_user_registration,
)
from utils import generate_code, is_admin

router = Router()

class RegistrationState(StatesGroup):
    awaiting_password = State()

@router.message(Command("register_nickname"))
async def register_by_admin(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    args = message.text.strip().split()
    if len(args) != 2:
        return await message.answer("⚠️ Использование: /register_nickname <ник>")

    nickname = args[1]
    async with SessionLocal() as db:
        taken = await db.scalar(select(User.id).where(User.nickname == nickname))
        if taken:
            return await message.reply("❌ Этот ник уже зарегистрирован.")

        code = generate_code()
        await insert_pending_registration(db, nickname, code, message.from_user.id)

    await message.answer(f"✅ Код регистрации для *{nickname}*:\n`{code}`", parse_mode="Markdown")


@router.message(Command("register"))
async def register_user(message: types.Message, state: FSMContext):
    args = message.text.strip().split()
    if len(args) != 2:
        return await message.answer("⚠️ Использование: /register <код>")

    code = args[1]
    async with SessionLocal() as db:
        if not await verify_registration_code(db, code):
            return await message.answer("❌ Код недействителен или устарел.")

    await state.update_data(code=code)
    await message.answer("🔐 Введите желаемый пароль:")
    await state.set_state(RegistrationState.awaiting_password)


@router.message(RegistrationState.awaiting_password)
async def receive_password(message: types.Message, state: FSMContext):
    password = message.text.strip()
    if len(password) < 8:
        return await message.answer("⚠️ Пароль должен быть не короче 8 символов.")

    data = await state.get_data()
    code = data.get("code")
    if not code:
        await state.clear()
        return await message.answer("❌ Ошибка: регистрационный код не найден.")

    async with SessionLocal() as db:
        ok, res = await complete_user_registration(db, message.from_user.id, code, password)

    if ok:
        await message.answer(f"🎉 Добро пожаловать в CrystalTrust, *{res['nickname']}*!", parse_mode="Markdown")
    else:
        await message.answer(f"❌ {res}")

    await state.clear()