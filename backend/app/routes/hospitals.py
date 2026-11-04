"""
HomeCare+ — Hospital Routes (PostgreSQL Edition)
GET /hospitals/nearby     — nearby hospitals (distance computed and sorted in SQL)
GET /hospitals/search     — search by name or specialty
GET /hospitals/{id}       — hospital detail
"""
import math
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.models import Hospital
from app.utils import escape_like

router = APIRouter()

EARTH_RADIUS_KM = 6371.0


def haversine(lat1, lon1, lat2, lon2) -> float:
    """Distance in km between two coordinates (pure-Python twin of the SQL expression)."""
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2) ** 2)
    return EARTH_RADIUS_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _distance_expr(lat: float, lng: float):
    """Haversine distance (km) from (lat, lng) to each hospital, as a SQL expression."""
    d_lat = func.radians(Hospital.latitude - lat) / 2
    d_lon = func.radians(Hospital.longitude - lng) / 2
    a = (func.power(func.sin(d_lat), 2)
         + func.cos(func.radians(lat)) * func.cos(func.radians(Hospital.latitude))
         * func.power(func.sin(d_lon), 2))
    return (2 * EARTH_RADIUS_KM * func.asin(func.least(1.0, func.sqrt(a)))).label("distance_km")


def hospital_dict(h: Hospital, distance_km: Optional[float] = None) -> dict:
    return {
        "id":          str(h.id),
        "name":        h.name,
        "type":        h.type,
        "address":     h.address,
        "city":        h.city,
        "phone":       h.phone,
        "website":     h.website,
        "latitude":    h.latitude,
        "longitude":   h.longitude,
        "specialties": list(h.specialties or []),
        "rating":      h.rating,
        "distance_km": round(distance_km, 2) if distance_km is not None else None,
    }


@router.get("/nearby")
async def get_nearby(
    lat:    float = Query(..., ge=-90, le=90, description="User latitude"),
    lng:    float = Query(..., ge=-180, le=180, description="User longitude"),
    radius: float = Query(10.0, gt=0, le=500, description="Search radius in km"),
    type:   Optional[str] = None,
    limit:  int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    # Cheap bounding-box prefilter (uses the lat/lng index), then exact haversine.
    d_lat = radius / 111.0
    d_lng = radius / max(111.0 * math.cos(math.radians(lat)), 1e-6)
    dist = _distance_expr(lat, lng)

    stmt = select(Hospital, dist).where(
        Hospital.is_active.is_(True),
        Hospital.latitude.is_not(None), Hospital.longitude.is_not(None),
        Hospital.latitude.between(lat - d_lat, lat + d_lat),
        Hospital.longitude.between(lng - d_lng, lng + d_lng),
        dist <= radius,
    )
    if type:
        stmt = stmt.where(Hospital.type == type)

    rows = (await db.execute(stmt.order_by(dist).limit(limit))).all()
    return {"hospitals": [hospital_dict(h, d) for h, d in rows], "radius_km": radius}


@router.get("/search")
async def search_hospitals(
    q: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    like = f"%{escape_like(q.strip())}%"
    # match the name, any specialty ("cardio" finds Cardiology) or the city
    specialty_hit = func.array_to_string(Hospital.specialties, " ").ilike(like, escape="\\")

    rows = (await db.execute(
        select(Hospital).where(
            Hospital.is_active.is_(True),
            or_(Hospital.name.ilike(like, escape="\\"), specialty_hit, Hospital.city.ilike(like, escape="\\")),
        ).order_by(func.similarity(Hospital.name, q).desc(), Hospital.rating.desc().nulls_last()).limit(20)
    )).scalars().all()
    return {"results": [hospital_dict(h) for h in rows]}


@router.get("/{hospital_id}")
async def get_hospital(hospital_id: str, db: AsyncSession = Depends(get_db)):
    h = None
    if hospital_id.isdigit() and len(hospital_id) < 10:
        h = await db.scalar(
            select(Hospital).where(Hospital.id == int(hospital_id), Hospital.is_active.is_(True))
        )
    if not h:
        raise HTTPException(status_code=404, detail="Hospital not found.")
    return hospital_dict(h)
