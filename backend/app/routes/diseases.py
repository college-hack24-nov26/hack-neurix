"""
HomeCare+ — Disease Library Routes (PostgreSQL Edition)
GET /diseases              — paginated list with filters
GET /diseases/search       — ranked search (name, ICD code, overview, symptoms, typos)
GET /diseases/organs       — list all organ systems (with disease counts)
GET /diseases/organ/{slug} — diseases by organ
GET /diseases/{id|slug}    — disease detail
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy import case, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.config.database import get_db
from app.models.models import Disease, DiseaseSymptom, OrganSystem, Symptom
from app.utils import escape_like

router = APIRouter()

_LOAD = (
    joinedload(Disease.organ_system),
    selectinload(Disease.symptom_links).joinedload(DiseaseSymptom.symptom),
)


def _symptom_names(d: Disease) -> List[str]:
    return [link.symptom.name.lower() for link in d.symptom_links]


def disease_summary(d: Disease) -> dict:
    return {
        "id":         str(d.id),
        "name":       d.name,
        "slug":       d.slug,
        "icd_code":   d.icd_code,
        "category":   d.category,
        "severity":   d.severity,
        "specialist": d.specialist,
        "symptoms":   _symptom_names(d),
        "organ":      d.organ_system.name if d.organ_system else None,
        "overview":   (d.overview or "")[:300],
    }


def disease_detail(d: Disease) -> dict:
    return {
        "id":              str(d.id),
        "name":            d.name,
        "slug":            d.slug,
        "icd_code":        d.icd_code,
        "category":        d.category,
        "severity":        d.severity,
        "overview":        d.overview,
        "symptoms":        _symptom_names(d),
        "causes":          list(d.causes or []),
        "risk_factors":    list(d.risk_factors or []),
        "complications":   list(d.complications or []),
        "treatments":      list(d.treatments or []),
        "medications":     list(d.medications or []),
        "home_remedies":   list(d.home_remedies or []),
        "prevention":      list(d.prevention or []),
        "precautions":     list(d.precautions or []),
        "specialist":      d.specialist,
        "specialist_type": d.specialist_type,
        "organ":           d.organ_system.name if d.organ_system else None,
        "is_dental":       d.is_dental,
    }


@router.get("")
async def list_diseases(
    page:     int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    category: Optional[str] = None,
    organ:    Optional[str] = None,
    severity: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    filters = []
    if category:
        filters.append(Disease.category.ilike(f"%{escape_like(category)}%", escape="\\"))
    if severity:
        filters.append(func.lower(Disease.severity) == severity.lower())
    if organ:
        organ_id = await db.scalar(select(OrganSystem.id).where(OrganSystem.slug == organ))
        if organ_id is None:
            return {"total": 0, "page": page, "per_page": per_page, "diseases": []}
        filters.append(Disease.organ_system_id == organ_id)

    total = await db.scalar(select(func.count()).select_from(Disease).where(*filters))
    rows = (await db.execute(
        select(Disease).where(*filters).options(*_LOAD)
        .order_by(Disease.name, Disease.id)
        .offset((page - 1) * per_page).limit(per_page)
    )).scalars().unique().all()

    return {
        "total": total,
        "page": page,
        "per_page": per_page,
        "diseases": [disease_summary(d) for d in rows],
    }


@router.get("/search")
async def search_diseases(
    q: str = Query(..., min_length=2),
    limit: int = Query(20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Ranked search. A disease matches if the query is in its name, ICD code,
    overview (full-text, stemmed), is close to the name (typo-tolerant), or is
    one of its symptoms. Name/ICD hits rank above symptom hits.
    """
    term = q.strip()
    like = f"%{escape_like(term)}%"
    prefix = f"{escape_like(term)}%"
    tsq = func.websearch_to_tsquery("english", term)

    symptom_hit = exists().where(
        DiseaseSymptom.disease_id == Disease.id,
        DiseaseSymptom.symptom_id == Symptom.id,
        Symptom.name.ilike(like, escape="\\"),
    )
    name_hit = Disease.name.ilike(like, escape="\\")
    icd_hit = Disease.icd_code.ilike(prefix, escape="\\")
    fts_hit = Disease.search_vector.op("@@")(tsq)
    fuzzy_hit = Disease.name.op("%")(term)

    score = (
        case((func.lower(Disease.name) == term.lower(), 10.0), else_=0.0)
        + case((Disease.name.ilike(prefix, escape="\\"), 4.0), (name_hit, 3.0), else_=0.0)
        + case((icd_hit, 4.0), else_=0.0)
        + func.ts_rank(Disease.search_vector, tsq) * 2.0
        + func.similarity(Disease.name, term) * 2.0
        + case((symptom_hit, 0.5), else_=0.0)
    ).label("score")

    rows = (await db.execute(
        select(Disease, score)
        .where(or_(name_hit, icd_hit, fts_hit, fuzzy_hit, symptom_hit))
        .options(*_LOAD)
        .order_by(score.desc(), Disease.name)
        .limit(limit)
    )).unique().all()

    return {"results": [disease_summary(d) for d, _ in rows], "query": q}


@router.get("/organs")
async def list_organs(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(OrganSystem, func.count(Disease.id))
        .outerjoin(Disease, Disease.organ_system_id == OrganSystem.id)
        .group_by(OrganSystem.id)
        .order_by(OrganSystem.name)
    )).all()

    return {"organs": [
        {
            "id":          str(o.id),
            "name":        o.name,
            "slug":        o.slug,
            "icon":        o.icon,
            "specialist":  o.specialist,
            "description": o.description,
            "count":       count,
        }
        for o, count in rows
    ]}


@router.get("/organ/{slug}")
async def diseases_by_organ(slug: str, db: AsyncSession = Depends(get_db)):
    organ = await db.scalar(select(OrganSystem).where(OrganSystem.slug == slug))
    if not organ:
        raise HTTPException(status_code=404, detail="Organ system not found.")

    diseases = (await db.execute(
        select(Disease).where(Disease.organ_system_id == organ.id)
        .options(*_LOAD).order_by(Disease.name)
    )).scalars().unique().all()

    return {
        "organ":    {"id": str(organ.id), "name": organ.name, "slug": organ.slug},
        "diseases": [disease_summary(d) for d in diseases],
    }


@router.get("/{disease_id}")
async def get_disease(disease_id: str, db: AsyncSession = Depends(get_db)):
    """Accepts the numeric id or the slug (e.g. /diseases/hypertension)."""
    cond = Disease.id == int(disease_id) if disease_id.isdigit() and len(disease_id) < 10 \
        else Disease.slug == disease_id.lower()

    disease = (await db.execute(
        select(Disease).where(cond).options(*_LOAD)
    )).unique().scalar_one_or_none()
    if not disease:
        raise HTTPException(status_code=404, detail="Disease not found.")
    return disease_detail(disease)
