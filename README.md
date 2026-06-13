# Personal Budget Maker API

A RESTful API for managing personal budgets — track income sources, categorize expenses, and generate period reports.

Built with **FastAPI** · **SQLAlchemy 2.x (async)** · **PostgreSQL / SQLite**

---

## Features

- **Flexible income tracking** — wages, side hustles, dividends, and miscellaneous sources; each with its own frequency (daily, weekly, biweekly, monthly) and a reference date for accurate period normalization
- **Customizable expense form** — 9 built-in categories and 54 line items out of the box; add, rename, hide, or reorder any item without losing the defaults (copy-on-write pattern)
- **Reset to defaults** — one call restores the original form structure for any user
- **Budget periods** — create budgets for any time window; all income is normalized to a monthly equivalent in reports regardless of pay frequency
- **JWT authentication** — register, log in, refresh tokens; all data is fully user-scoped

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | FastAPI 0.115 |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL (production) · SQLite (local dev) |
| Migrations | Alembic |
| Auth | JWT (python-jose) · bcrypt (passlib) |
| Validation | Pydantic v2 |
| Server | Uvicorn |

---

## Live Docs

Interactive Swagger UI — register an account and explore all endpoints directly in the browser.

> **https://personal-budget-maker.onrender.com/docs**

---

## Getting Started

### Prerequisites

- Python 3.11+
- (Optional) Docker — only needed for a local PostgreSQL instance

### Quickstart with SQLite (zero config)

```bash
git clone https://github.com/laislodi/personal-budget-maker.git
cd personal-budget-maker

pip install -r requirements.txt
cp .env.example .env

python -m seed.defaults          # loads 9 default expense categories + 54 items
uvicorn app.main:app --reload    # → http://localhost:8000/docs
```

### Local setup with PostgreSQL (Docker)

```bash
cp .env.example .env
# Edit .env: uncomment the POSTGRES_* variables and the PostgreSQL DATABASE_URL

docker compose up -d             # starts Postgres on localhost:5432

python -m seed.defaults
uvicorn app.main:app --reload
```

---

## Environment Variables

Copy `.env.example` to `.env` and fill in the values. Never commit `.env`.

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | SQLAlchemy async connection string | `sqlite+aiosqlite:///./budget.db` |
| `POSTGRES_USER` | PostgreSQL username (Docker Compose only) | — |
| `POSTGRES_PASSWORD` | PostgreSQL password (Docker Compose only) | — |
| `POSTGRES_DB` | PostgreSQL database name (Docker Compose only) | — |
| `SECRET_KEY` | JWT signing secret — **change in production** | dev placeholder |
| `ALGORITHM` | JWT algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token lifetime | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token lifetime | `7` |

---

## API Overview

Full interactive documentation is available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create an account |
| `POST` | `/auth/login` | Get access + refresh tokens |
| `GET` | `/auth/me` | Current user info |

### Income Sources

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/income-sources` | List all active income sources |
| `POST` | `/income-sources` | Add an income source |
| `GET` | `/income-sources/{id}` | Get a single source |
| `PUT` | `/income-sources/{id}` | Update amount, frequency, or reference date |
| `DELETE` | `/income-sources/{id}` | Soft-delete (deactivate) |

### Expense Form

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/categories` | Full form structure with all items (overrides applied) |
| `POST` | `/categories` | Add a custom category |
| `PUT` | `/categories/{id}` | Rename or reorder a custom category |
| `DELETE` | `/categories/{id}` | Delete a custom category |
| `GET` | `/categories/{id}/items` | List items in a category |
| `POST` | `/categories/{id}/items` | Add a custom item |
| `PUT` | `/items/{id}` | Rename or reorder (copy-on-write for system defaults) |
| `DELETE` | `/items/{id}` | Hide a default item or delete a custom item |
| `POST` | `/items/reset-defaults` | Restore the original form structure |

### Budgets

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/budgets` | List all budgets |
| `POST` | `/budgets` | Create a budget period |
| `GET` | `/budgets/{id}` | Get a budget |
| `PUT` | `/budgets/{id}` | Update budget metadata |
| `DELETE` | `/budgets/{id}` | Delete a budget |
| `GET` | `/budgets/{id}/income` | List income entries |
| `PUT` | `/budgets/{id}/income/{source_id}` | Set or update an income value |
| `DELETE` | `/budgets/{id}/income/{source_id}` | Remove an income entry |
| `GET` | `/budgets/{id}/expenses` | List expense entries |
| `PUT` | `/budgets/{id}/expenses/{item_id}` | Set or update an expense value |
| `DELETE` | `/budgets/{id}/expenses/{item_id}` | Remove an expense entry |
| `GET` | `/budgets/{id}/report` | Full report with totals and per-category breakdown |

---

## Running Tests

The test suite uses [pytest](https://pytest.org) with async support via `pytest-asyncio`. Each test runs against a fresh in-memory SQLite database — no external services required.

### Install test dependencies

```bash
pip install -r requirements-dev.txt
```

### Run all tests

```bash
pytest
```

### Run with verbose output

```bash
pytest -v
```

### Test structure

```
tests/
├── conftest.py              # shared fixtures: async client, seeded DB, auth headers
├── unit/
│   ├── test_income_service.py   # frequency → monthly normalization, period conversion
│   └── test_report_service.py  # report builder: grouping, net calc, multi-source income
└── integration/
    ├── test_categories.py       # category/item CRUD, copy-on-write overrides, reset-defaults
    └── test_budgets.py          # budget CRUD, income/expense entries, report calculations
```

Unit tests cover the service layer directly (no HTTP, no database). Integration tests hit the full FastAPI stack via `httpx.AsyncClient`.

---

## Income Frequency Normalization

When generating a report, all income sources are converted to a **monthly equivalent** regardless of pay frequency:

| Frequency | Monthly multiplier |
|---|---|
| Daily | × 30 |
| Weekly | × 52 ÷ 12 ≈ × 4.33 |
| Biweekly | × 26 ÷ 12 ≈ × 2.17 |
| Monthly | × 1 |

A biweekly paycheck of $2,000, for example, appears as ~$4,333/month in the report — giving an accurate picture regardless of how each income source is paid.

---

## Project Structure

```
app/
├── main.py               # entry point, lifespan hook, middleware
├── config.py             # settings loaded from environment variables
├── database.py           # async engine + session factory
├── dependencies.py       # JWT auth dependency injection
├── models/
│   ├── enums.py          # IncomeType, Frequency
│   ├── user.py
│   ├── income.py         # IncomeSource
│   ├── expense.py        # ExpenseCategory, ExpenseItem, UserItemOverride
│   └── budget.py         # Budget, BudgetIncomeEntry, BudgetExpenseEntry
├── schemas/              # Pydantic request/response models
├── routers/
│   ├── auth.py
│   ├── income.py
│   ├── categories.py     # copy-on-write form customization
│   └── budgets.py        # entries + report endpoint
└── services/
    ├── auth.py           # JWT creation + bcrypt
    ├── income.py         # frequency → monthly normalization
    └── report.py         # report builder

seed/defaults.py          # idempotent seed: 9 categories, 54 items
alembic/                  # database migrations
docker-compose.yml        # local PostgreSQL via Docker
render.yaml               # Render deployment blueprint
```

---

## Deployment

The repo ships with a `render.yaml` Blueprint for one-click deployment to [Render](https://render.com):

1. Create a free account at **render.com** (sign up with GitHub)
2. Dashboard → **New → Blueprint** → connect `laislodi/personal-budget-maker`
3. Render automatically provisions the web service and a free PostgreSQL database
4. The seed script runs on every deploy (idempotent — safe to re-run)
5. Live docs available at `https://<your-service>.onrender.com/docs`

---

## License

MIT
