from datetime import datetime, timedelta, timezone
import bcrypt
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import PendingRegistration, User, Account
from services.account import generate_account_id


async def insert_pending_registration(db: AsyncSession, nickname: str, code: str, issued_by: int) -> None:
    expires = datetime.now(timezone.utc) + timedelta(minutes=15)
    db.add(PendingRegistration(nickname=nickname, code=code, issued_by=str(issued_by), expires_at=expires))
    await db.commit()


async def verify_registration_code(db: AsyncSession, code: str) -> PendingRegistration | None:
    return await db.scalar(
        select(PendingRegistration)
        .where(
    PendingRegistration.code == code,
    PendingRegistration.expires_at > text("(now() AT TIME ZONE 'utc')")

)
    )


async def complete_user_registration(db: AsyncSession, tg_id: int, code: str, password: str):
    pending = await db.scalar(
    select(PendingRegistration)
    .where(PendingRegistration.code == code,PendingRegistration.expires_at >text("(now() AT TIME ZONE 'utc')")
)
    )
    if not pending:
        return False, "Код недействителен или устарел."

    exists = await db.scalar(select(User.id).where(User.tg_id == tg_id))
    if exists:
        return False, "Вы уже зарегистрированы."

    nick_taken = await db.scalar(select(User.id).where(User.nickname == pending.nickname))
    if nick_taken:
        return False, f"Ник {pending.nickname} занят."

    pwd_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(tg_id=tg_id, nickname=pending.nickname, password_hash=pwd_hash)
    db.add(user)
    await db.flush()

    acc_public_id = await generate_account_id(db, "personal")
    acc = Account(account_id=acc_public_id, owner_id=user.id, account_type='personal', balance=0)
    db.add(acc)

    pending.tg_id = tg_id
    await db.delete(pending)

    await db.commit()

    return True, {"nickname": user.nickname, "user_id": user.id, "account_id": acc_public_id}
