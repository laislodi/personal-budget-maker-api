import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.budget import Budget, BudgetIncomeEntry, BudgetExpenseEntry
from app.models.income import IncomeSource
from app.models.expense import ExpenseItem
from app.models.user import User
from app.schemas.budget import BudgetCreate, BudgetUpdate, IncomeEntryUpsert, ExpenseEntryUpsert, BudgetResponse
from app.schemas.report import BudgetReportResponse, ReportIncomeEntry, ReportExpenseItem, ReportCategorySummary
from app.dependencies import get_current_user
from app.services.report import build_report


router = APIRouter(prefix="/budgets", tags=["budgets"])


async def _get_budget(budget_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession) -> Budget:
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget


@router.get("", response_model=list[BudgetResponse])
async def list_budgets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget).where(Budget.user_id == current_user.id).order_by(Budget.period_start.desc())
    )
    return result.scalars().all()


@router.post("", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
async def create_budget(
    payload: BudgetCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    budget = Budget(
        user_id=current_user.id,
        name=payload.name,
        period_type=payload.period_type,
        period_start=payload.period_start,
        period_end=payload.period_end,
    )
    db.add(budget)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.get("/{budget_id}", response_model=BudgetResponse)
async def get_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _get_budget(budget_id, current_user.id, db)


@router.put("/{budget_id}", response_model=BudgetResponse)
async def update_budget(
    budget_id: uuid.UUID,
    payload: BudgetUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    budget = await _get_budget(budget_id, current_user.id, db)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(budget, field, value)
    await db.commit()
    await db.refresh(budget)
    return budget


@router.delete("/{budget_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_budget(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    budget = await _get_budget(budget_id, current_user.id, db)
    await db.delete(budget)
    await db.commit()


# --- Income entries ---

@router.get("/{budget_id}/income", response_model=list[dict])
async def list_income_entries(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)
    result = await db.execute(
        select(BudgetIncomeEntry)
        .where(BudgetIncomeEntry.budget_id == budget_id)
        .options(selectinload(BudgetIncomeEntry.income_source))
    )
    entries = result.scalars().all()
    return [
        {
            "income_source_id": str(e.income_source_id),
            "name": e.income_source.name,
            "type": e.income_source.type,
            "amount": e.amount,
            "notes": e.notes,
        }
        for e in entries
    ]


@router.put("/{budget_id}/income/{source_id}", status_code=status.HTTP_200_OK)
async def upsert_income_entry(
    budget_id: uuid.UUID,
    source_id: uuid.UUID,
    payload: IncomeEntryUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)

    src_result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == source_id, IncomeSource.user_id == current_user.id
        )
    )
    if not src_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found")

    entry_result = await db.execute(
        select(BudgetIncomeEntry).where(
            BudgetIncomeEntry.budget_id == budget_id,
            BudgetIncomeEntry.income_source_id == source_id,
        )
    )
    entry = entry_result.scalar_one_or_none()
    if entry:
        entry.amount = payload.amount
        entry.notes = payload.notes
    else:
        entry = BudgetIncomeEntry(
            budget_id=budget_id,
            income_source_id=source_id,
            amount=payload.amount,
            notes=payload.notes,
        )
        db.add(entry)

    await db.commit()
    return {"status": "ok"}


@router.delete("/{budget_id}/income/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income_entry(
    budget_id: uuid.UUID,
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)
    result = await db.execute(
        select(BudgetIncomeEntry).where(
            BudgetIncomeEntry.budget_id == budget_id,
            BudgetIncomeEntry.income_source_id == source_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry:
        await db.delete(entry)
        await db.commit()


# --- Expense entries ---

@router.get("/{budget_id}/expenses", response_model=list[dict])
async def list_expense_entries(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)
    result = await db.execute(
        select(BudgetExpenseEntry)
        .where(BudgetExpenseEntry.budget_id == budget_id)
        .options(
            selectinload(BudgetExpenseEntry.expense_item).selectinload(ExpenseItem.category)
        )
    )
    entries = result.scalars().all()
    return [
        {
            "expense_item_id": str(e.expense_item_id),
            "category": e.expense_item.category.name,
            "name": e.expense_item.name,
            "amount": e.amount,
            "is_fixed": e.is_fixed,
            "notes": e.notes,
        }
        for e in entries
    ]


@router.put("/{budget_id}/expenses/{item_id}", status_code=status.HTTP_200_OK)
async def upsert_expense_entry(
    budget_id: uuid.UUID,
    item_id: uuid.UUID,
    payload: ExpenseEntryUpsert,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)

    item_result = await db.execute(select(ExpenseItem).where(ExpenseItem.id == item_id))
    if not item_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense item not found")

    entry_result = await db.execute(
        select(BudgetExpenseEntry).where(
            BudgetExpenseEntry.budget_id == budget_id,
            BudgetExpenseEntry.expense_item_id == item_id,
        )
    )
    entry = entry_result.scalar_one_or_none()
    if entry:
        entry.amount = payload.amount
        entry.is_fixed = payload.is_fixed
        entry.notes = payload.notes
    else:
        entry = BudgetExpenseEntry(
            budget_id=budget_id,
            expense_item_id=item_id,
            amount=payload.amount,
            is_fixed=payload.is_fixed,
            notes=payload.notes,
        )
        db.add(entry)

    await db.commit()
    return {"status": "ok"}


@router.delete("/{budget_id}/expenses/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_expense_entry(
    budget_id: uuid.UUID,
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _get_budget(budget_id, current_user.id, db)
    result = await db.execute(
        select(BudgetExpenseEntry).where(
            BudgetExpenseEntry.budget_id == budget_id,
            BudgetExpenseEntry.expense_item_id == item_id,
        )
    )
    entry = result.scalar_one_or_none()
    if entry:
        await db.delete(entry)
        await db.commit()


# --- Report ---

@router.get("/{budget_id}/report", response_model=BudgetReportResponse)
async def get_report(
    budget_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Budget)
        .where(Budget.id == budget_id, Budget.user_id == current_user.id)
        .options(
            selectinload(Budget.income_entries).selectinload(BudgetIncomeEntry.income_source),
            selectinload(Budget.expense_entries)
            .selectinload(BudgetExpenseEntry.expense_item)
            .selectinload(ExpenseItem.category),
        )
    )
    budget = result.scalar_one_or_none()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")

    report = build_report(budget)

    return BudgetReportResponse(
        budget_id=report.budget_id,
        budget_name=report.budget_name,
        period_type=report.period_type,
        period_start=report.period_start,
        period_end=report.period_end,
        total_income=report.total_income,
        total_expenses=report.total_expenses,
        net=report.net,
        income_entries=[ReportIncomeEntry(**e) for e in report.income_entries],
        categories=[
            ReportCategorySummary(
                category_id=c.category_id,
                category_name=c.category_name,
                total=c.total,
                items=[ReportExpenseItem(**vars(i)) for i in c.items],
            )
            for c in report.categories
        ],
    )
