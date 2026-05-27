from decimal import Decimal
from app.models.enums import Frequency


# Multipliers to convert any frequency to a monthly equivalent
_TO_MONTHLY: dict[Frequency, Decimal] = {
    Frequency.DAILY: Decimal("30"),
    Frequency.WEEKLY: Decimal("52") / Decimal("12"),
    Frequency.BIWEEKLY: Decimal("26") / Decimal("12"),
    Frequency.MONTHLY: Decimal("1"),
}


def to_monthly_equivalent(amount: Decimal, frequency: Frequency) -> Decimal:
    return (amount * _TO_MONTHLY[frequency]).quantize(Decimal("0.01"))


def to_period_equivalent(amount: Decimal, source_frequency: Frequency, target_frequency: Frequency) -> Decimal:
    """Convert an amount from source_frequency to target_frequency."""
    monthly = to_monthly_equivalent(amount, source_frequency)
    return (monthly / _TO_MONTHLY[target_frequency]).quantize(Decimal("0.01"))
