"""
HomeCare+ — Health Metrics Routes (PostgreSQL Edition)
POST /health/metrics               — log one or more vitals
GET  /health/metrics               — latest reading of every vital
GET  /health/metrics/{type}        — history for one vital
GET  /health/dashboard             — latest vitals + 7-day heart-rate trend + score
"""
import logging
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_current_user
from app.models.models import HealthMetric, User, utcnow
from app.utils import iso

logger = logging.getLogger(__name__)
router = APIRouter()

METRIC_UNITS = {
    "heart_rate":   "bpm",
    "systolic_bp":  "mmHg",
    "diastolic_bp": "mmHg",
    "oxygen_level": "%",
    "blood_sugar":  "mg/dL",
    "bmi":          "",
    "weight":       "kg",
    "steps":        "",
    "temperature":  "°C",
}

NORMAL_RANGES = {
    "heart_rate":   (60,   100),
    "systolic_bp":  (90,   120),
    "diastolic_bp": (60,    80),
    "oxygen_level": (95,   100),
    "blood_sugar":  (70,   100),
    "bmi":          (18.5, 24.9),
    "temperature":  (36.1, 37.2),
}


def get_status(metric_type: str, value: float) -> str:
    if metric_type not in NORMAL_RANGES:
        return "unknown"
    lo, hi = NORMAL_RANGES[metric_type]
    if value < lo:
        return "low"
    if value > hi:
        return "high"
    return "normal"


_F = dict(default=None, allow_inf_nan=False)


class MetricLogRequest(BaseModel):
    heart_rate:   Optional[float] = Field(**_F)
    systolic_bp:  Optional[float] = Field(**_F)
    diastolic_bp: Optional[float] = Field(**_F)
    oxygen_level: Optional[float] = Field(**_F)
    blood_sugar:  Optional[float] = Field(**_F)
    bmi:          Optional[float] = Field(**_F)
    weight:       Optional[float] = Field(**_F)
    steps:        Optional[float] = Field(**_F)
    temperature:  Optional[float] = Field(**_F)
    notes:        Optional[str]   = None


async def _latest_per_type(db: AsyncSession, user_id) -> Dict[str, HealthMetric]:
    """Latest reading of each vital in ONE query (DISTINCT ON), not one per vital."""
    rows = (await db.execute(
        select(HealthMetric).where(HealthMetric.user_id == user_id)
        .distinct(HealthMetric.metric_type)
        .order_by(HealthMetric.metric_type, HealthMetric.recorded_at.desc(), HealthMetric.id.desc())
    )).scalars().all()
    by_type = {m.metric_type: m for m in rows}
    return {mt: by_type[mt] for mt in METRIC_UNITS if mt in by_type}     # stable order


@router.post("/metrics")
async def log_metrics(
    body: MetricLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    payload = body.model_dump(exclude={"notes"}, exclude_none=True)
    if not payload:
        raise HTTPException(status_code=400, detail="At least one metric value is required.")

    saved, rows = [], []
    now = utcnow()
    for metric_type, value in payload.items():
        if metric_type not in METRIC_UNITS:
            continue
        rows.append(HealthMetric(
            user_id=current_user.id, metric_type=metric_type, value=float(value),
            unit=METRIC_UNITS[metric_type], notes=body.notes, recorded_at=now,
        ))
        saved.append({
            "type":   metric_type,
            "value":  value,
            "unit":   METRIC_UNITS[metric_type],
            "status": get_status(metric_type, value),
        })

    try:
        db.add_all(rows)
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.error(f"Error saving metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to save metrics.")

    logger.info(f"Saved {len(saved)} metrics for user {current_user.id}")
    return {"saved": saved, "count": len(saved), "message": "Vitals saved successfully"}


@router.get("/metrics")
async def get_latest_metrics(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    latest = await _latest_per_type(db, current_user.id)
    return {"metrics": {
        mt: {
            "value":       m.value,
            "unit":        m.unit or "",
            "status":      get_status(mt, m.value),
            "recorded_at": iso(m.recorded_at),
        }
        for mt, m in latest.items()
    }}


@router.get("/metrics/{metric_type}")
async def get_metric_history(
    metric_type: str,
    days: int = Query(7, ge=1, le=90),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if metric_type not in METRIC_UNITS:
        raise HTTPException(status_code=400, detail=f"Unknown metric type: {metric_type}")

    since = datetime.now(timezone.utc) - timedelta(days=days)
    readings = (await db.execute(
        select(HealthMetric).where(
            HealthMetric.user_id == current_user.id,
            HealthMetric.metric_type == metric_type,
            HealthMetric.recorded_at >= since,
        ).order_by(HealthMetric.recorded_at).limit(10000)
    )).scalars().all()

    return {
        "metric_type": metric_type,
        "unit":        METRIC_UNITS[metric_type],
        "days":        days,
        "readings": [
            {
                "value":       r.value,
                "status":      get_status(metric_type, r.value),
                "recorded_at": iso(r.recorded_at),
                "notes":       r.notes,
            }
            for r in readings
        ],
    }


@router.get("/dashboard")
async def get_dashboard(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    since_week = datetime.now(timezone.utc) - timedelta(days=7)

    latest_rows = await _latest_per_type(db, current_user.id)
    latest = {
        mt: {"value": m.value, "unit": m.unit or "", "status": get_status(mt, m.value)}
        for mt, m in latest_rows.items()
    }

    hr_trend = (await db.execute(
        select(HealthMetric.value, HealthMetric.recorded_at).where(
            HealthMetric.user_id == current_user.id,
            HealthMetric.metric_type == "heart_rate",
            HealthMetric.recorded_at >= since_week,
        ).order_by(HealthMetric.recorded_at).limit(1000)
    )).all()

    def compute_score(metrics: Dict[str, dict]) -> int:
        if not metrics:
            return 0
        normal = sum(1 for m in metrics.values() if m.get("status") == "normal")
        return round((normal / len(metrics)) * 100)

    return {
        "latest_vitals":    latest,
        "heart_rate_trend": [{"value": v, "date": iso(t)} for v, t in hr_trend],
        "health_score":     compute_score(latest),
    }
