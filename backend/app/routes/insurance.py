"""
HomeCare+ — Insurance Policy Routes (PostgreSQL Edition)
GET    /insurance           — list user's policies
POST   /insurance           — add a policy
PUT    /insurance/{id}      — update a policy
DELETE /insurance/{id}      — delete a policy
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_current_user, parse_uuid
from app.models.models import InsurancePolicy, User
from app.utils import iso

router = APIRouter()


def _blank_to_none(v):
    return None if isinstance(v, str) and not v.strip() else v


class PolicyCreate(BaseModel):
    provider:      str
    policyNumber:  str
    type:          Optional[str] = "Individual"
    coverage:      Optional[str] = None
    premium:       Optional[str] = None
    renewalDate:   Optional[date] = None
    notes:         Optional[str] = None

    @field_validator("renewalDate", "coverage", "premium", "notes", mode="before")
    @classmethod
    def _blank(cls, v):
        return _blank_to_none(v)


class PolicyUpdate(BaseModel):
    provider:     Optional[str]  = None
    policyNumber: Optional[str]  = None
    type:         Optional[str]  = None
    coverage:     Optional[str]  = None
    premium:      Optional[str]  = None
    renewalDate:  Optional[date] = None
    status:       Optional[str]  = None
    notes:        Optional[str]  = None

    @field_validator("renewalDate", mode="before")
    @classmethod
    def _blank(cls, v):
        return _blank_to_none(v)


def policy_dict(p: InsurancePolicy) -> dict:
    return {
        "id":           str(p.id),
        "provider":     p.provider,
        "policyNumber": p.policy_number,
        "type":         p.policy_type,
        "coverage":     p.coverage,
        "premium":      p.premium,
        "renewalDate":  iso(p.renewal_date),
        "status":       p.status,
        "notes":        p.notes,
        "createdAt":    iso(p.created_at),
    }


async def _get_owned(db: AsyncSession, policy_id: str, user: User) -> InsurancePolicy:
    pid = parse_uuid(policy_id)
    policy = None
    if pid is not None:
        policy = await db.scalar(
            select(InsurancePolicy).where(InsurancePolicy.id == pid, InsurancePolicy.user_id == user.id)
        )
    if not policy:
        raise HTTPException(status_code=404, detail="Policy not found.")
    return policy


_DUPLICATE = HTTPException(status_code=409, detail="You already have a policy with this number.")


@router.get("")
async def list_policies(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policies = (await db.execute(
        select(InsurancePolicy).where(InsurancePolicy.user_id == current_user.id)
        .order_by(InsurancePolicy.created_at.desc()).limit(1000)
    )).scalars().all()
    return {"policies": [policy_dict(p) for p in policies]}


@router.post("", status_code=status.HTTP_201_CREATED)
async def add_policy(
    body: PolicyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy = InsurancePolicy(
        user_id=current_user.id,
        provider=body.provider,
        policy_number=body.policyNumber,
        policy_type=body.type,
        coverage=body.coverage,
        premium=body.premium,
        renewal_date=body.renewalDate,
        status="active",
        notes=body.notes,
    )
    db.add(policy)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise _DUPLICATE
    return policy_dict(policy)


@router.put("/{policy_id}")
async def update_policy(
    policy_id: str,
    body: PolicyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy = await _get_owned(db, policy_id, current_user)

    if body.provider     is not None: policy.provider      = body.provider
    if body.policyNumber is not None: policy.policy_number = body.policyNumber
    if body.type         is not None: policy.policy_type   = body.type
    if body.coverage     is not None: policy.coverage      = body.coverage
    if body.premium      is not None: policy.premium       = body.premium
    if body.renewalDate  is not None: policy.renewal_date  = body.renewalDate
    if body.status       is not None: policy.status        = body.status
    if body.notes        is not None: policy.notes         = body.notes

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise _DUPLICATE
    await db.refresh(policy)
    return policy_dict(policy)


@router.delete("/{policy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_policy(
    policy_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    policy = await _get_owned(db, policy_id, current_user)
    await db.delete(policy)
    await db.commit()
