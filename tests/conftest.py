import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app as fastapi_app
from app.database import Base, get_db
from app.models.expense import ExpenseCategory, ExpenseItem
import app.models  # noqa — registers all models with metadata

_DEFAULT_CATEGORIES = [
    ("Home", ["Mortgage/Rent", "Insurance", "Repairs", "Services",
               "Utilities - Gas", "Utilities - Electricity", "Utilities - Water",
               "Utilities - Internet", "Utilities - Phone"]),
    ("Daily Living", ["Groceries", "Child Care", "Dry Cleaning", "Dining Out",
                      "Housecleaning Service", "Dog Walker"]),
    ("Transportation", ["Gas/Fuel", "Insurance", "Repairs", "Car Wash/Detailing",
                        "Parking", "Public Transportation"]),
    ("Entertainment", ["Cable TV", "Video/DVD Rentals", "Movies/Plays", "Concerts/Clubs"]),
    ("Health", ["Health Club Dues", "Insurance", "Prescriptions", "Over-the-Counter Drugs",
                "Veterinarians/Pet Medicines", "Gym Fees", "Sports Equipment"]),
    ("Vacations", ["Plane Fare", "Accommodations", "Food", "Souvenirs", "Pet Boarding", "Rental Car"]),
    ("Subscriptions", ["Netflix", "Disney+", "Apple TV", "Magazines", "Newspaper"]),
    ("Personal", ["Clothing", "Gifts", "Salon/Barber", "Books", "Music"]),
    ("Financial Obligations", ["Long-term Savings", "Retirement - 401k", "Retirement - Roth IRA",
                                "Credit Card Payments", "Income Tax (Additional)", "Other Obligations"]),
]


@pytest_asyncio.fixture
async def client():
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with session_factory() as session:
        for order, (cat_name, item_names) in enumerate(_DEFAULT_CATEGORIES):
            cat = ExpenseCategory(name=cat_name, display_order=order, is_default=True, user_id=None)
            session.add(cat)
            await session.flush()
            for item_order, item_name in enumerate(item_names):
                session.add(ExpenseItem(
                    category_id=cat.id, name=item_name,
                    display_order=item_order, is_default=True, user_id=None,
                ))
        await session.commit()

    async def override_get_db():
        async with session_factory() as session:
            yield session

    fastapi_app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=fastapi_app), base_url="http://test") as ac:
        yield ac

    fastapi_app.dependency_overrides.clear()
    await engine.dispose()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient):
    await client.post("/auth/register", json={
        "email": "testuser@example.com",
        "name": "Test User",
        "password": "password123",
    })
    res = await client.post("/auth/login", json={
        "email": "testuser@example.com",
        "password": "password123",
    })
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
