from decimal import Decimal
from types import SimpleNamespace
from app.models.enums import Frequency, IncomeType
from app.services.report import build_report


def _category(cat_id, name):
    return SimpleNamespace(id=cat_id, name=name)


def _item(item_id, name, category):
    return SimpleNamespace(id=item_id, name=name, category=category)


def _source(source_id, name, frequency, income_type=IncomeType.WAGES):
    return SimpleNamespace(id=source_id, name=name, frequency=frequency, type=income_type)


def _budget(income_entries, expense_entries):
    return SimpleNamespace(
        id="budget-1",
        name="Test Budget",
        period_type=Frequency.MONTHLY,
        period_start="2026-06-01",
        period_end="2026-06-30",
        income_entries=income_entries,
        expense_entries=expense_entries,
    )


def test_empty_budget():
    report = build_report(_budget([], []))
    assert report.total_income == Decimal("0")
    assert report.total_expenses == Decimal("0")
    assert report.net == Decimal("0")
    assert report.income_entries == []
    assert report.categories == []


def test_monthly_income_passes_through():
    source = _source("s1", "Salary", Frequency.MONTHLY)
    entry = SimpleNamespace(income_source=source, amount=Decimal("5000"), notes=None)

    report = build_report(_budget([entry], []))

    assert report.total_income == Decimal("5000.00")
    assert report.income_entries[0]["monthly_equivalent"] == Decimal("5000.00")


def test_weekly_income_is_normalized():
    source = _source("s1", "Freelance", Frequency.WEEKLY, IncomeType.SIDE_HUSTLE)
    entry = SimpleNamespace(income_source=source, amount=Decimal("1200"), notes=None)

    report = build_report(_budget([entry], []))

    # 1200 * 52 / 12 = 5200
    assert report.total_income == Decimal("5200.00")


def test_expenses_grouped_by_category():
    cat = _category("c1", "Home")
    item1 = _item("i1", "Rent", cat)
    item2 = _item("i2", "Insurance", cat)
    entries = [
        SimpleNamespace(expense_item=item1, amount=Decimal("1500"), is_fixed=True, notes=None),
        SimpleNamespace(expense_item=item2, amount=Decimal("200"), is_fixed=True, notes=None),
    ]

    report = build_report(_budget([], entries))

    assert len(report.categories) == 1
    assert report.categories[0].category_name == "Home"
    assert report.categories[0].total == Decimal("1700")
    assert len(report.categories[0].items) == 2


def test_expenses_across_multiple_categories():
    cat1 = _category("c1", "Home")
    cat2 = _category("c2", "Transportation")
    entries = [
        SimpleNamespace(expense_item=_item("i1", "Rent", cat1), amount=Decimal("1500"), is_fixed=True, notes=None),
        SimpleNamespace(expense_item=_item("i2", "Gas", cat2), amount=Decimal("300"), is_fixed=False, notes=None),
    ]

    report = build_report(_budget([], entries))

    assert len(report.categories) == 2
    assert report.total_expenses == Decimal("1800")


def test_net_equals_income_minus_expenses():
    source = _source("s1", "Salary", Frequency.MONTHLY)
    income_entry = SimpleNamespace(income_source=source, amount=Decimal("5000"), notes=None)

    cat = _category("c1", "Home")
    expense_entry = SimpleNamespace(
        expense_item=_item("i1", "Rent", cat), amount=Decimal("1500"), is_fixed=True, notes=None
    )

    report = build_report(_budget([income_entry], [expense_entry]))

    assert report.net == Decimal("3500.00")


def test_multiple_income_sources_sum():
    entries = [
        SimpleNamespace(
            income_source=_source("s1", "Job", Frequency.MONTHLY), amount=Decimal("3000"), notes=None
        ),
        SimpleNamespace(
            income_source=_source("s2", "Side gig", Frequency.MONTHLY), amount=Decimal("500"), notes=None
        ),
    ]

    report = build_report(_budget(entries, []))

    assert report.total_income == Decimal("3500.00")
    assert len(report.income_entries) == 2
