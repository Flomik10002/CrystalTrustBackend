from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Text, TIMESTAMP, text, CheckConstraint, ForeignKey, Index, func

from database.engine import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint("status IN ('pending', 'confirmed', 'cancelled')", name="chk_tx_status"),
        Index("ix_transactions_code", "confirmation_code"),
        Index("ix_transactions_status", "status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    source_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    target_account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    amount: Mapped[int]
    status: Mapped[str] = mapped_column(String, server_default=text("'confirmed'"), nullable=False)
    initiated_by_user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())
    confirmed_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    confirmation_code: Mapped[str] = mapped_column(nullable=True)
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), nullable=True)
    initiator = relationship("User", back_populates="transactions")
