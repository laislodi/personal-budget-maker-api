"""
Populate the database with system default expense categories and items.

Usage:
    python -m seed.defaults

Safe to re-run: skips seeding if defaults already exist.
"""
import asyncio
from app.database import AsyncSessionLocal, engine, Base
from app.models.expense import ExpenseCategory, ExpenseItem
from sqlalchemy import select


DEFAULT_CATEGORIES: list[tuple[str, list[str]]] = [
    ("Home", [
        "Mortgage/Rent",
        "Insurance",
        "Repairs",
        "Services",
        "Utilities - Gas",
        "Utilities - Electricity",
        "Utilities - Water",
        "Utilities - Internet",
        "Utilities - Phone",
    ]),
    ("Daily Living", [
        "Groceries",
        "Child Care",
        "Dry Cleaning",
        "Dining Out",
        "Housecleaning Service",
        "Dog Walker",
    ]),
    ("Transportation", [
        "Gas/Fuel",
        "Insurance",
        "Repairs",
        "Car Wash/Detailing",
        "Parking",
        "Public Transportation",
    ]),
    ("Entertainment", [
        "Cable TV",
        "Video/DVD Rentals",
        "Movies/Plays",
        "Concerts/Clubs",
    ]),
    ("Health", [
        "Health Club Dues",
        "Insurance",
        "Prescriptions",
        "Over-the-Counter Drugs",
        "Veterinarians/Pet Medicines",
        "Gym Fees",
        "Sports Equipment",
    ]),
    ("Vacations", [
        "Plane Fare",
        "Accommodations",
        "Food",
        "Souvenirs",
        "Pet Boarding",
        "Rental Car",
    ]),
    ("Subscriptions", [
        "Netflix",
        "Disney+",
        "Apple TV",
        "Magazines",
        "Newspaper",
    ]),
    ("Personal", [
        "Clothing",
        "Gifts",
        "Salon/Barber",
        "Books",
        "Music",
    ]),
    ("Financial Obligations", [
        "Long-term Savings",
        "Retirement - 401k",
        "Retirement - Roth IRA",
        "Credit Card Payments",
        "Income Tax (Additional)",
        "Other Obligations",
    ]),
]


async def seed() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        existing = await db.execute(
            select(ExpenseCategory).where(ExpenseCategory.is_default == True).limit(1)
        )
        if existing.scalar_one_or_none():
            print("Default categories already seeded — skipping.")
            return

        for order, (cat_name, item_names) in enumerate(DEFAULT_CATEGORIES):
            cat = ExpenseCategory(
                name=cat_name,
                display_order=order,
                is_default=True,
                user_id=None,
            )
            db.add(cat)
            await db.flush()

            for item_order, item_name in enumerate(item_names):
                db.add(
                    ExpenseItem(
                        category_id=cat.id,
                        name=item_name,
                        display_order=item_order,
                        is_default=True,
                        user_id=None,
                    )
                )

        await db.commit()
        print(f"Seeded {len(DEFAULT_CATEGORIES)} categories with all default items.")


if __name__ == "__main__":
    asyncio.run(seed())
