from decimal import Decimal
from app.models.enums import Frequency
from app.services.income import to_monthly_equivalent, to_period_equivalent


def test_monthly_stays_unchanged():
    assert to_monthly_equivalent(Decimal("1000"), Frequency.MONTHLY) == Decimal("1000.00")


def test_daily_to_monthly():
    assert to_monthly_equivalent(Decimal("100"), Frequency.DAILY) == Decimal("3000.00")


def test_weekly_to_monthly():
    # 1200 * 52 / 12 = 5200.00
    assert to_monthly_equivalent(Decimal("1200"), Frequency.WEEKLY) == Decimal("5200.00")


def test_biweekly_to_monthly():
    # 2600 * 26 / 12 = 5633.33
    assert to_monthly_equivalent(Decimal("2600"), Frequency.BIWEEKLY) == Decimal("5633.33")


def test_to_period_equivalent_monthly_to_weekly():
    # 5200/month → 5200 * 12 / 52 = 1200/week
    assert to_period_equivalent(Decimal("5200"), Frequency.MONTHLY, Frequency.WEEKLY) == Decimal("1200.00")


def test_to_period_equivalent_same_frequency():
    assert to_period_equivalent(Decimal("500"), Frequency.WEEKLY, Frequency.WEEKLY) == Decimal("500.00")


def test_to_period_equivalent_monthly_to_biweekly():
    # 2600/month → monthly = 2600, biweekly = 2600 / (26/12) = 2600 * 12/26 = 1200
    assert to_period_equivalent(Decimal("1200"), Frequency.MONTHLY, Frequency.BIWEEKLY) == Decimal("553.85")
