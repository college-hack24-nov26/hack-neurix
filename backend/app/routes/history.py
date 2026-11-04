from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import User, UserActivity

router = APIRouter()


class ActivityCreate(BaseModel):
    action: str
    title: str
    details: Optional[dict] = None
    route: Optional[str] = None


@router.get("")
async def get_history(
    limit: int = Query(100, ge=1, le=500),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(UserActivity)
        .where(UserActivity.user_id == current_user.id)
        .order_by(UserActivity.created_at.desc())
        .limit(limit)
    )
    rows = result.scalars().all()
    return {
        "items": [
            {
                "id": str(row.id),
                "action": row.action,
                "title": row.title,
                "details": row.details or {},
                "route": row.route,
                "created_at": row.created_at.isoformat(),
            }
            for row in rows
        ]
    }


@router.post("")
async def add_activity(
    body: ActivityCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    item = UserActivity(
        user_id=current_user.id,
        action=body.action[:100],
        title=body.title[:255],
        details=body.details,
        route=body.route[:255] if body.route else None,
    )
    db.add(item)
    await db.commit()
    await db.refresh(item)
    return {"id": str(item.id)}


@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        delete(UserActivity).where(
            UserActivity.id == activity_id,
            UserActivity.user_id == current_user.id,
        )
    )
    await db.commit()
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="History item not found")
    return {"deleted": True}


@router.delete("")
async def clear_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(delete(UserActivity).where(UserActivity.user_id == current_user.id))
    await db.commit()
    return {"deleted": True}
