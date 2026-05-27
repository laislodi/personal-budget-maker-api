from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, Date, DateTime, ForeignKey, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import IncomeType, Frequency


class IncomeSource(Base):
    __tablename__ = "income_sources"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    type: Mapped[IncomeType] = mapped_column(SAEnum(IncomeType, native_enum=False, length=32))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    is_fixed: Mapped[bool] = mapped_column(Boolean, default=True)
    frequency: Mapped[Frequency] = mapped_column(
        SAEnum(Frequency, native_enum=False, length=16), default=Frequency.MONTHLY
    )
    reference_date: Mapped[date] = mapped_column(Date)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="income_sources")
    budget_entries: Mapped[list[BudgetIncomeEntry]] = relationship(back_populates="income_source")


from app.models.user import User  # noqa: E402, F401
from app.models.budget import BudgetIncomeEntry  # noqa: E402, F401
