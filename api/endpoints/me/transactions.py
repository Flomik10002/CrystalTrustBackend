# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy import select
# from sqlalchemy.ext.asyncio import AsyncSession
# from datetime import datetime
# from collections import defaultdict
# from sqlalchemy.orm import aliased
# from zoneinfo import ZoneInfo  # stdlib
#
# from api.auth import get_current_user
# from database.deps import get_session
# from database.models import User, Account, Transaction
# from settings import a_settings
#
# router = APIRouter(prefix="/me")
#
# MONTHS_NOMINATIVE = [
#     "", "января", "февраля", "марта", "апреля", "мая", "июня",
#     "июля", "августа", "сентября", "октября", "ноября", "декабря"
# ]
#
#
# def fmt_acc(num: int) -> str:
#     width = 3 if num < 1000 else 4
#     return f"crystal-{num:0{width}}"
#
#
# def to_local(dt: datetime) -> datetime:
#     if dt.tzinfo is None:
#         dt = dt.replace(tzinfo=timezone.utc)
#     return dt.astimezone(PARIS_TZ)
#
# def pretty_label(d: datetime) -> str:
#     today = datetime.now(PARIS_TZ).date()
#     if d.date() == today:
#         return "Сегодня"
#     if d.date() == (today.replace(day=today.day) - (today - today)):  # no-op, оставлено для читаемости
#         pass
#     label = f"{d.day} {MONTHS_NOMINATIVE[d.month]}"
#     if d.year != today.year:
#         label += f" {d.year}"
#     return label
#
# @router.get("/transactions")
# async def get_transactions(
#     user=Depends(get_current_user),
#     db: AsyncSession = Depends(get_session),
# ):
#     uid = await db.scalar(select(User.id).where(User.tg_id == user["id"]))
#     if not uid:
#         raise HTTPException(404, "User not found")
#
#     sa, ta = aliased(Account), aliased(Account)
#
#     q = (
#         select(
#             Transaction.id,
#             Transaction.amount,
#             Transaction.created_at,
#             Transaction.source_account_id,
#             Transaction.target_account_id,
#             sa.account_id.label("source_public"),
#             ta.account_id.label("target_public"),
#             sa.owner_id.label("source_owner"),
#             ta.owner_id.label("target_owner"),
#             select(User.nickname).where(User.id == sa.owner_id).scalar_subquery().label("from_nick"),
#             select(User.nickname).where(User.id == ta.owner_id).scalar_subquery().label("to_nick"),
#         )
#         .outerjoin(sa, sa.id == Transaction.source_account_id)
#         .outerjoin(ta, ta.id == Transaction.target_account_id)
#         .where(
#             ((sa.owner_id == uid) | (ta.owner_id == uid)) &
#             (Transaction.status == "confirmed")
#         )
#         .order_by(Transaction.created_at.desc())
#     )
#
#     rows = (await db.execute(q)).all()
#
#     grouped: dict[str, list] = defaultdict(list)
#     totals: dict[str, int] = defaultdict(int)
#
#     def push(
#         dt: datetime,
#         amount: int,
#         row,
#         type_: str,
#         from_nick: str,
#         to_nick: str,
#         from_acc: str,
#         to_acc: str,
#         avatar: str,
#         *,
#         total_delta: int | None = None,      # сколько учитывать в dailyTotal (по умолчанию amount)
#         name_override: str | None = None,    # переопределить отображаемое имя
#     ):
#         key = f"{dt.day} {MONTHS_NOMINATIVE[dt.month]}"
#         totals[key] += amount if total_delta is None else total_delta
#
#         grouped[key].append({
#             "id": f"tx{row.id}",
#             "name": name_override if name_override is not None else (to_nick if amount > 0 else from_nick),
#             "amount": amount,
#             "type": type_,
#             "from": from_nick,
#             "from_account": from_acc,
#             "to": to_nick,
#             "to_account": to_acc,
#             "avatar": avatar,
#             "timestamp": dt.isoformat(),
#         })
#
#     for r in rows:
#         out = r.source_owner == uid
#         inn = r.target_owner == uid
#         internal = out and inn
#
#         is_deposit = r.source_public == a_settings.BANK_ACCOUNT_ID and inn
#         is_withdraw = r.target_public == a_settings.BANK_ACCOUNT_ID and out
#
#         if is_deposit:
#             push(
#                 r.created_at, r.amount, r, "",
#                 a_settings.BANK_NICK, r.to_nick,
#                 "", fmt_acc(r.target_public),
#                 a_settings.BANK_AVATAR,
#                 total_delta=0,
#                 name_override="Пополнение"
#             )
#             continue
#
#         if is_withdraw:
#             push(
#                 r.created_at, -r.amount, r, "",
#                 r.from_nick, a_settings.BANK_NICK,
#                 fmt_acc(r.source_public), '',
#                 a_settings.BANK_AVATAR,
#                 total_delta=0,
#                 name_override="Снятие"
#             )
#             continue
#
#         if internal:
#             push(
#                 r.created_at, r.amount, r, ''+fmt_acc(r.source_public)+" ->",
#                 r.from_nick, r.to_nick,
#                 fmt_acc(r.source_public), fmt_acc(r.target_public),
#                 a_settings.BANK_AVATAR,
#                 total_delta=0,
#                 name_override="Между счетами"
#             )
#         else:
#             if out:
#                 avatar_nick = r.to_nick
#                 amount = -r.amount
#             else:
#                 avatar_nick = r.from_nick
#                 amount = +r.amount
#
#             push(
#                 r.created_at, amount, r, "Перевод",
#                 r.from_nick, r.to_nick,
#                 fmt_acc(r.source_public), fmt_acc(r.target_public),
#                 f"https://mc-heads.net/avatar/{avatar_nick}",
#                 name_override=avatar_nick
#             )
#
#     return [
#         {
#             "date": d,
#             "dailyTotal": f"{'' if totals[d] < 0 else '+'}{totals[d]} АР",
#             "items": grouped[d],
#         }
#         for d in sorted(grouped.keys(), reverse=True)
#     ]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from collections import defaultdict
from sqlalchemy.orm import aliased
from zoneinfo import ZoneInfo  # stdlib

from api.auth import get_current_user
from database.deps import get_session
from database.models import User, Account, Transaction
from settings import a_settings

router = APIRouter(prefix="/me")

MONTHS_NOMINATIVE = [
    "", "января", "февраля", "марта", "апреля", "мая", "июня",
    "июля", "августа", "сентября", "октября", "ноября", "декабря"
]

Moscow_TZ = ZoneInfo("Europe/Moscow")

def fmt_acc(num: int) -> str:
    width = 3 if num < 1000 else 4
    return f"crystal-{num:0{width}}"

def to_local(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(Moscow_TZ)

def pretty_label(d: datetime) -> str:
    today = datetime.now(Moscow_TZ).date()
    if d.date() == today:
        return "Сегодня"
    if d.date() == (today.replace(day=today.day) - (today - today)):  # no-op, оставлено для читаемости
        pass
    label = f"{d.day} {MONTHS_NOMINATIVE[d.month]}"
    if d.year != today.year:
        label += f" {d.year}"
    return label

@router.get("/transactions")
async def get_transactions(
    user=Depends(get_current_user),
    db: AsyncSession = Depends(get_session),
):
    uid = await db.scalar(select(User.id).where(User.tg_id == user["id"]))
    if not uid:
        raise HTTPException(404, "User not found")

    sa, ta = aliased(Account), aliased(Account)

    q = (
        select(
            Transaction.id,
            Transaction.amount,
            Transaction.created_at,
            Transaction.source_account_id,
            Transaction.target_account_id,
            sa.account_id.label("source_public"),
            ta.account_id.label("target_public"),
            sa.owner_id.label("source_owner"),
            ta.owner_id.label("target_owner"),
            select(User.nickname).where(User.id == sa.owner_id).scalar_subquery().label("from_nick"),
            select(User.nickname).where(User.id == ta.owner_id).scalar_subquery().label("to_nick"),
        )
        .outerjoin(sa, sa.id == Transaction.source_account_id)
        .outerjoin(ta, ta.id == Transaction.target_account_id)
        .where(
            ((sa.owner_id == uid) | (ta.owner_id == uid)) &
            (Transaction.status == "confirmed")
        )
        .order_by(Transaction.created_at.desc())
    )

    rows = (await db.execute(q)).all()

    grouped: dict[str, dict] = defaultdict(lambda: {"label": "", "items": []})
    totals: dict[str, int] = defaultdict(int)

    def push(
        dt_utc: datetime,
        amount: int,
        row,
        type_: str,
        from_nick: str,
        to_nick: str,
        from_acc: str,
        to_acc: str,
        avatar: str,
        *,
        total_delta: int | None = None,
        name_override: str | None = None,
    ):
        dt = to_local(dt_utc)
        date_key = dt.date().isoformat()  # YYYY-MM-DD — корректная, устойчивая группировка
        if not grouped[date_key]["label"]:
            grouped[date_key]["label"] = pretty_label(dt)

        totals[date_key] += amount if total_delta is None else total_delta

        grouped[date_key]["items"].append({
            "id": f"tx{row.id}",
            "name": name_override if name_override is not None else (to_nick if amount > 0 else from_nick),
            "amount": amount,
            "type": type_,
            "from": from_nick,
            "from_account": from_acc,
            "to": to_nick,
            "to_account": to_acc,
            "avatar": avatar,
            "timestamp": dt.isoformat(),
        })

    for r in rows:
        out = r.source_owner == uid
        inn = r.target_owner == uid
        internal = out and inn

        is_deposit = (r.source_public == a_settings.BANK_ACCOUNT_ID) and inn
        is_withdraw = (r.target_public == a_settings.BANK_ACCOUNT_ID) and out

        if is_deposit:
            push(
                r.created_at, r.amount, r, "",
                a_settings.BANK_NICK, r.to_nick,
                "", fmt_acc(r.target_public),
                a_settings.BANK_AVATAR,
                total_delta=0,
                name_override="Пополнение"
            )
            continue

        if is_withdraw:
            push(
                r.created_at, -r.amount, r, "",
                r.from_nick, a_settings.BANK_NICK,
                fmt_acc(r.source_public), "",
                a_settings.BANK_AVATAR,
                total_delta=0,
                name_override="Снятие"
            )
            continue

        if internal:
            push(
                r.created_at, r.amount, r, f'{fmt_acc(r.source_public)} ->',
                r.from_nick, r.to_nick,
                fmt_acc(r.source_public), fmt_acc(r.target_public),
                a_settings.BANK_AVATAR,
                total_delta=0,
                name_override="Между счетами"
            )
        else:
            if out:
                avatar_nick = r.to_nick
                amount = -r.amount
            else:
                avatar_nick = r.from_nick
                amount = +r.amount

            push(
                r.created_at, amount, r, "Перевод",
                r.from_nick, r.to_nick,
                fmt_acc(r.source_public), fmt_acc(r.target_public),
                f"https://mc-heads.net/avatar/{avatar_nick}",
                name_override=avatar_nick
            )

    sorted_keys = sorted(grouped.keys(), reverse=True)
    return [
        {
            "date": grouped[k]["label"],
            "dailyTotal": f"{'' if totals[k] < 0 else '+'}{totals[k]} АР",
            "items": grouped[k]["items"],  # уже в порядке .order_by(created_at desc)
        }
        for k in sorted_keys
    ]
