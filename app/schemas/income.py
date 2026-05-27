import uuid
from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel, field_validator
from app.models.enums import IncomeType, Frequency


class IncomeSourceCreate(BaseModel):
    name: str
    type: IncomeType
    amount: Decimal
    frequency: Frequency = Frequency.MONTHLY
    reference_date: date
    # If omitted: WAGES defaults to fixed=True, SIDE_HUSTLE to fixed=False, others to True
    is_fixed: bool | None = None

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v


class IncomeSourceUpdate(BaseModel):
    name: str | None = None
    amount: Decimal | None = None
    frequency: Frequency | None = None
    reference_date: date | None = None
    is_fixed: bool | None = None
    is_active: bool | None = None


class IncomeSourceResponse(BaseModel):
    id: uuid.UUID
    name: str
    type: IncomeType
    amount: Decimal
    is_fixed: bool
    frequency: Frequency
    reference_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
