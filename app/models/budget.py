from __future__ import annotations

import uuid
from datetime import datetime, date
from decimal import Decimal
from sqlalchemy import String, Boolean, Numeric, Date, DateTime, ForeignKey, Text, func, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
from app.models.enums import Frequency


class Budget(Base):
    __tablename__ = "budgets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255))
    period_type: Mapped[Frequency] = mapped_column(SAEnum(Frequency, native_enum=False, length=16))
    period_start: Mapped[date] = mapped_column(Date)
    period_end: Mapped[date] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped[User] = relationship(back_populates="budgets")
    income_entries: Mapped[list[BudgetIncomeEntry]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )
    expense_entries: Mapped[list[BudgetExpenseEntry]] = relationship(
        back_populates="budget", cascade="all, delete-orphan"
    )


class BudgetIncomeEntry(Base):
    __tablename__ = "budget_income_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), index=True)
    income_source_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("income_sources.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    budget: Mapped[Budget] = relationship(back_populates="income_entries")
    income_source: Mapped[IncomeSource] = relationship(back_populates="budget_entries")


class BudgetExpenseEntry(Base):
    __tablename__ = "budget_expense_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    budget_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("budgets.id", ondelete="CASCADE"), index=True)
    expense_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_items.id", ondelete="CASCADE"), index=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    # Overrides the item's fixed/variable nature for this specific budget period
    is_fixed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    budget: Mapped[Budget] = relationship(back_populates="expense_entries")
    expense_item: Mapped[ExpenseItem] = relationship(back_populates="budget_entries")


from app.models.user import User  # noqa: E402, F401
from app.models.income import IncomeSource  # noqa: E402, F401
from app.models.expense import ExpenseItem  # noqa: E402, F401
