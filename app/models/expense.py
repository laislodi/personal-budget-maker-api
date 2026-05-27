from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, ForeignKey, DateTime, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ExpenseCategory(Base):
    __tablename__ = "expense_categories"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # NULL = system default shared across all users
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[list[ExpenseItem]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )


class ExpenseItem(Base):
    __tablename__ = "expense_items"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_categories.id", ondelete="CASCADE"), index=True
    )
    # NULL = system default; set to user_id for user-created items
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255))
    display_order: Mapped[int] = mapped_column(Integer, default=0)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[ExpenseCategory] = relationship(back_populates="items")
    overrides: Mapped[list[UserItemOverride]] = relationship(
        back_populates="expense_item", cascade="all, delete-orphan"
    )
    budget_entries: Mapped[list[BudgetExpenseEntry]] = relationship(back_populates="expense_item")


class UserItemOverride(Base):
    """
    Copy-on-write overrides for system default expense items.

    Users never mutate system rows. Renaming, hiding, or reordering a default item
    writes here instead. Deleting all overrides for a user resets their form to defaults.
    """

    __tablename__ = "user_item_overrides"
    __table_args__ = (UniqueConstraint("user_id", "expense_item_id"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    expense_item_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("expense_items.id", ondelete="CASCADE"), index=True
    )
    is_hidden: Mapped[bool] = mapped_column(Boolean, default=False)
    custom_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)

    user: Mapped[User] = relationship(back_populates="item_overrides")
    expense_item: Mapped[ExpenseItem] = relationship(back_populates="overrides")


from app.models.user import User  # noqa: E402, F401
from app.models.budget import BudgetExpenseEntry  # noqa: E402, F401
