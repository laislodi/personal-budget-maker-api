from decimal import Decimal
from pydantic import BaseModel
from app.models.enums import Frequency, IncomeType


class ReportIncomeEntry(BaseModel):
    income_source_id: str
    name: str
    type: IncomeType
    amount: Decimal
    frequency: Frequency
    monthly_equivalent: Decimal
    notes: str | None = None


class ReportExpenseItem(BaseModel):
    expense_item_id: str
    name: str
    amount: Decimal
    is_fixed: bool | None = None
    notes: str | None = None


class ReportCategorySummary(BaseModel):
    category_id: str
    category_name: str
    total: Decimal
    items: list[ReportExpenseItem]


class BudgetReportResponse(BaseModel):
    budget_id: str
    budget_name: str
    period_type: Frequency
    period_start: str
    period_end: str
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    income_entries: list[ReportIncomeEntry]
    categories: list[ReportCategorySummary]
