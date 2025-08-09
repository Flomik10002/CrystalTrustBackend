from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, TIMESTAMP, Integer, func

from database.engine import Base


class PendingRegistration(Base):
    __tablename__ = "pending_registrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nickname: Mapped[str] = mapped_column(String)
    tg_id: Mapped[int] = mapped_column(Integer, nullable=True)
    code: Mapped[str] = mapped_column(String, index=True)
    issued_by: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=False)
