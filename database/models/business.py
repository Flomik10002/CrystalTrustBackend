from datetime import datetime

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, CheckConstraint, TIMESTAMP, ForeignKey, text, func

from database.engine import Base


class Business(Base):
    __tablename__ = "businesses"
    __table_args__ = (
        CheckConstraint("tag ~ '^[a-z0-9_]+$'", name="chk_business_tag"),
        CheckConstraint("category IN ('build', 'industrial', 'store', 'casino', 'entertainment', 'other')", name="chk_business_category"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id", ondelete="CASCADE"), unique=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String, nullable=False)
    tag: Mapped[str] = mapped_column(String, unique=True)
    category: Mapped[str] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=True), server_default=func.now())

    account = relationship("Account", back_populates="business")
    owner = relationship("User", back_populates="businesses")
