import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.income import IncomeSource
from app.models.user import User
from app.models.enums import IncomeType
from app.schemas.income import IncomeSourceCreate, IncomeSourceUpdate, IncomeSourceResponse
from app.dependencies import get_current_user


router = APIRouter(prefix="/income-sources", tags=["income"])


def _default_is_fixed(income_type: IncomeType) -> bool:
    return income_type != IncomeType.SIDE_HUSTLE


@router.get("", response_model=list[IncomeSourceResponse])
async def list_income_sources(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncomeSource)
        .where(IncomeSource.user_id == current_user.id, IncomeSource.is_active == True)
        .order_by(IncomeSource.created_at)
    )
    return result.scalars().all()


@router.post("", response_model=IncomeSourceResponse, status_code=status.HTTP_201_CREATED)
async def create_income_source(
    payload: IncomeSourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    is_fixed = payload.is_fixed if payload.is_fixed is not None else _default_is_fixed(payload.type)
    source = IncomeSource(
        user_id=current_user.id,
        name=payload.name,
        type=payload.type,
        amount=payload.amount,
        frequency=payload.frequency,
        reference_date=payload.reference_date,
        is_fixed=is_fixed,
    )
    db.add(source)
    await db.commit()
    await db.refresh(source)
    return source


@router.get("/{source_id}", response_model=IncomeSourceResponse)
async def get_income_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == source_id, IncomeSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found")
    return source


@router.put("/{source_id}", response_model=IncomeSourceResponse)
async def update_income_source(
    source_id: uuid.UUID,
    payload: IncomeSourceUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == source_id, IncomeSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found")

    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)
    return source


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_income_source(
    source_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(IncomeSource).where(
            IncomeSource.id == source_id, IncomeSource.user_id == current_user.id
        )
    )
    source = result.scalar_one_or_none()
    if not source:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income source not found")
    source.is_active = False
    await db.commit()
