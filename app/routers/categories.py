import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.expense import ExpenseCategory, ExpenseItem, UserItemOverride
from app.models.user import User
from app.schemas.expense import (
    CategoryCreate,
    CategoryUpdate,
    ItemCreate,
    ItemOverrideUpdate,
    CategoryResponse,
    ItemResponse,
)
from app.dependencies import get_current_user


router = APIRouter(tags=["categories"])


async def _build_category_view(user_id: uuid.UUID, db: AsyncSession) -> list[CategoryResponse]:
    """
    Merge system defaults and user-owned items, applying copy-on-write overrides.
    Hidden items are excluded; renamed items show the custom name.
    """
    result = await db.execute(
        select(ExpenseCategory)
        .where(or_(ExpenseCategory.user_id == None, ExpenseCategory.user_id == user_id))
        .options(
            selectinload(ExpenseCategory.items).selectinload(ExpenseItem.overrides)
        )
        .order_by(ExpenseCategory.display_order, ExpenseCategory.created_at)
    )
    categories = result.scalars().all()

    output: list[CategoryResponse] = []
    for cat in categories:
        items_out: list[ItemResponse] = []

        sorted_items = sorted(cat.items, key=lambda i: i.display_order)
        for item in sorted_items:
            # Skip items belonging to other users
            if item.user_id is not None and item.user_id != user_id:
                continue

            override = next((o for o in item.overrides if o.user_id == user_id), None)
            if override and override.is_hidden:
                continue

            effective_name = override.custom_name if (override and override.custom_name) else item.name
            effective_order = (
                override.display_order
                if (override and override.display_order is not None)
                else item.display_order
            )

            items_out.append(
                ItemResponse(
                    id=item.id,
                    name=effective_name,
                    display_order=effective_order,
                    is_default=item.is_default,
                    is_hidden=False,
                    category_id=item.category_id,
                )
            )

        output.append(
            CategoryResponse(
                id=cat.id,
                name=cat.name,
                display_order=cat.display_order,
                is_default=cat.is_default,
                items=items_out,
            )
        )
    return output


@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await _build_category_view(current_user.id, db)


@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cat = ExpenseCategory(user_id=current_user.id, name=payload.name, display_order=payload.display_order)
    db.add(cat)
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse(id=cat.id, name=cat.name, display_order=cat.display_order, is_default=False, items=[])


@router.put("/categories/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.user_id == current_user.id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or is a system default (cannot be mutated directly)",
        )
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(cat, field, value)
    await db.commit()
    await db.refresh(cat)
    return CategoryResponse(id=cat.id, name=cat.name, display_order=cat.display_order, is_default=False, items=[])


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            ExpenseCategory.user_id == current_user.id,
        )
    )
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or is a system default",
        )
    await db.delete(cat)
    await db.commit()


@router.get("/categories/{category_id}/items", response_model=list[ItemResponse])
async def list_items(
    category_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    view = await _build_category_view(current_user.id, db)
    for cat in view:
        if cat.id == category_id:
            return cat.items
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")


@router.post("/categories/{category_id}/items", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    category_id: uuid.UUID,
    payload: ItemCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cat_result = await db.execute(
        select(ExpenseCategory).where(
            ExpenseCategory.id == category_id,
            or_(ExpenseCategory.user_id == None, ExpenseCategory.user_id == current_user.id),
        )
    )
    if not cat_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

    item = ExpenseItem(
        category_id=category_id,
        user_id=current_user.id,
        name=payload.name,
        display_order=payload.display_order,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return ItemResponse(
        id=item.id,
        name=item.name,
        display_order=item.display_order,
        is_default=False,
        is_hidden=False,
        category_id=category_id,
    )


@router.put("/items/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: uuid.UUID,
    payload: ItemOverrideUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ExpenseItem).where(ExpenseItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.user_id == current_user.id:
        # User-owned item: mutate directly
        if payload.custom_name is not None:
            item.name = payload.custom_name
        if payload.display_order is not None:
            item.display_order = payload.display_order
        await db.commit()
        await db.refresh(item)
        return ItemResponse(
            id=item.id,
            name=item.name,
            display_order=item.display_order,
            is_default=False,
            is_hidden=False,
            category_id=item.category_id,
        )

    # System default: copy-on-write via UserItemOverride
    override_result = await db.execute(
        select(UserItemOverride).where(
            UserItemOverride.user_id == current_user.id,
            UserItemOverride.expense_item_id == item_id,
        )
    )
    override = override_result.scalar_one_or_none()
    if override is None:
        override = UserItemOverride(user_id=current_user.id, expense_item_id=item_id)
        db.add(override)

    if payload.custom_name is not None:
        override.custom_name = payload.custom_name
    if payload.is_hidden is not None:
        override.is_hidden = payload.is_hidden
    if payload.display_order is not None:
        override.display_order = payload.display_order

    await db.commit()
    await db.refresh(override)

    return ItemResponse(
        id=item.id,
        name=override.custom_name or item.name,
        display_order=override.display_order if override.display_order is not None else item.display_order,
        is_default=item.is_default,
        is_hidden=override.is_hidden,
        category_id=item.category_id,
    )


@router.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(ExpenseItem).where(ExpenseItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")

    if item.user_id == current_user.id:
        await db.delete(item)
    else:
        # System default: set is_hidden=True in the override
        override_result = await db.execute(
            select(UserItemOverride).where(
                UserItemOverride.user_id == current_user.id,
                UserItemOverride.expense_item_id == item_id,
            )
        )
        override = override_result.scalar_one_or_none()
        if override is None:
            override = UserItemOverride(user_id=current_user.id, expense_item_id=item_id, is_hidden=True)
            db.add(override)
        else:
            override.is_hidden = True

    await db.commit()


@router.post("/items/reset-defaults", status_code=status.HTTP_204_NO_CONTENT)
async def reset_to_defaults(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove all overrides and custom items/categories, restoring the system defaults."""
    overrides = await db.execute(
        select(UserItemOverride).where(UserItemOverride.user_id == current_user.id)
    )
    for override in overrides.scalars():
        await db.delete(override)

    custom_items = await db.execute(
        select(ExpenseItem).where(ExpenseItem.user_id == current_user.id)
    )
    for item in custom_items.scalars():
        await db.delete(item)

    custom_cats = await db.execute(
        select(ExpenseCategory).where(ExpenseCategory.user_id == current_user.id)
    )
    for cat in custom_cats.scalars():
        await db.delete(cat)

    await db.commit()
