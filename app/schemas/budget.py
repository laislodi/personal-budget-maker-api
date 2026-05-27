import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, model_validator
from app.models.enums import Frequency


class BudgetCreate(BaseModel):
    name: str
    period_type: Frequency
    period_start: date
    period_end: date

    @model_validator(mode="after")
    def end_after_start(self) -> "BudgetCreate":
        if self.period_end <= self.period_start:
            raise ValueError("period_end must be after period_start")
        return self


class BudgetUpdate(BaseModel):
    name: str | None = None
    period_type: Frequency | None = None
    period_start: date | None = None
    period_end: date | None = None


class IncomeEntryUpsert(BaseModel):
    amount: Decimal
    notes: str | None = None


class ExpenseEntryUpsert(BaseModel):
    amount: Decimal
    is_fixed: bool | None = None
    notes: str | None = None


class BudgetResponse(BaseModel):
    id: uuid.UUID
    name: str
    period_type: Frequency
    period_start: date
    period_end: date
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
