from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import Account


async def get_accounts_by_owner(db: AsyncSession, owner_id: int) -> list[Account]:
    result = await db.scalars(select(Account).where(Account.owner_id == owner_id))
    return list(result)

async def generate_account_id(db: AsyncSession, account_type: str) -> int:
    if account_type not in ("personal", "business"):
        raise ValueError("Unknown account type")

    base = 1001 if account_type == "business" else 1

    q = (
        select(Account.account_id)
        .where(Account.account_type == account_type, Account.account_id >= base)
        .order_by(Account.account_id)
        .with_for_update()
    )
    used_ids = list(await db.scalars(q))

    next_id = base
    for acc_id in used_ids:
        if acc_id == next_id:
            next_id += 1
        elif acc_id > next_id:
            break

    return next_id
