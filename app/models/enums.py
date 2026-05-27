from enum import Enum


class IncomeType(str, Enum):
    WAGES = "WAGES"
    INTEREST_DIVIDEND = "INTEREST_DIVIDEND"
    SIDE_HUSTLE = "SIDE_HUSTLE"
    MISCELLANEOUS = "MISCELLANEOUS"


class Frequency(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    BIWEEKLY = "BIWEEKLY"
    MONTHLY = "MONTHLY"
