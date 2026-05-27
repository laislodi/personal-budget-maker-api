from __future__ import annotations

import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    income_sources: Mapped[list[IncomeSource]] = relationship(back_populates="user")
    budgets: Mapped[list[Budget]] = relationship(back_populates="user")
    item_overrides: Mapped[list[UserItemOverride]] = relationship(back_populates="user")


# Avoid circular import at module level — resolved by SQLAlchemy at mapper config time
from app.models.income import IncomeSource  # noqa: E402, F401
from app.models.budget import Budget  # noqa: E402, F401
from app.models.expense import UserItemOverride  # noqa: E402, F401
