from dataclasses import dataclass, field
from decimal import Decimal
from app.models.enums import Frequency, IncomeType
from app.services.income import to_monthly_equivalent


@dataclass
class ReportItem:
    expense_item_id: str
    name: str
    amount: Decimal
    is_fixed: bool | None
    notes: str | None


@dataclass
class CategorySummary:
    category_id: str
    category_name: str
    total: Decimal = field(default_factory=lambda: Decimal("0"))
    items: list[ReportItem] = field(default_factory=list)


@dataclass
class BudgetReport:
    budget_id: str
    budget_name: str
    period_type: Frequency
    period_start: str
    period_end: str
    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    income_entries: list[dict]
    categories: list[CategorySummary]


def build_report(budget) -> BudgetReport:
    income_entries = []
    total_income = Decimal("0")

    for entry in budget.income_entries:
        source = entry.income_source
        monthly = to_monthly_equivalent(entry.amount, source.frequency)
        income_entries.append({
            "income_source_id": str(source.id),
            "name": source.name,
            "type": source.type,
            "amount": entry.amount,
            "frequency": source.frequency,
            "monthly_equivalent": monthly,
            "notes": entry.notes,
        })
        total_income += monthly

    categories: dict[str, CategorySummary] = {}
    total_expenses = Decimal("0")

    for entry in budget.expense_entries:
        item = entry.expense_item
        cat = item.category
        cat_id = str(cat.id)

        if cat_id not in categories:
            categories[cat_id] = CategorySummary(category_id=cat_id, category_name=cat.name)

        categories[cat_id].items.append(
            ReportItem(
                expense_item_id=str(item.id),
                name=item.name,
                amount=entry.amount,
                is_fixed=entry.is_fixed,
                notes=entry.notes,
            )
        )
        categories[cat_id].total += entry.amount
        total_expenses += entry.amount

    return BudgetReport(
        budget_id=str(budget.id),
        budget_name=budget.name,
        period_type=budget.period_type,
        period_start=str(budget.period_start),
        period_end=str(budget.period_end),
        total_income=total_income,
        total_expenses=total_expenses,
        net=total_income - total_expenses,
        income_entries=income_entries,
        categories=list(categories.values()),
    )
