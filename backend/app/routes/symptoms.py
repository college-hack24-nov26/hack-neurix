"""
HomeCare+ — Symptom Checker Routes (PostgreSQL Edition)
POST /symptoms/analyze    — analyze symptoms (LLM first, SQL-scored disease library as fallback)
GET  /symptoms/list       — symptom catalogue (typeahead / quick-pick chips)
POST /symptoms/followup   — get follow-up questions
"""
import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.middleware.auth import get_optional_user
from app.models.models import SymptomCheck, Symptom, User
from app.services.symptom_db_service import predict_from_db
from app.services.symptom_service import SymptomAnalyzer
from app.utils import escape_like

logger = logging.getLogger(__name__)
router = APIRouter()
analyzer = SymptomAnalyzer()


class AnalyzeRequest(BaseModel):
    symptoms:  List[str]
    follow_up: Optional[Dict[str, Any]] = {}
    language:  Optional[str] = "en"

    @field_validator("symptoms")
    @classmethod
    def symptoms_not_empty(cls, v):
        if not v:
            raise ValueError("At least one symptom is required.")
        cleaned = [s.strip() for s in v if s and s.strip()]
        if not cleaned:
            raise ValueError("Symptoms must be non-empty strings.")
        return cleaned[:15]  # cap at 15


class FollowUpRequest(BaseModel):
    symptoms:  List[str]
    step:      int = 0


@router.post("/analyze")
async def analyze_symptoms(
    body: AnalyzeRequest,
    current_user: Optional[User] = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    language = (body.language or "en").lower()
    follow_up = body.follow_up or {}

    # 1) Real AI analysis first (OpenAI -> Anthropic -> Groq).
    #    The LLM client is synchronous, so run it in a worker thread instead of
    #    freezing the event loop for the whole request.
    results = None
    ai_powered = False
    try:
        results = await run_in_threadpool(
            analyzer.analyze_with_ai, body.symptoms, follow_up, language=language
        )
        if results:
            ai_powered = True
    except Exception as e:
        logger.error(f"AI symptom analysis failed: {e}")

    # 2) Fall back to scoring the whole disease library in PostgreSQL.
    if not results:
        try:
            results = await predict_from_db(db, body.symptoms, follow_up)
        except Exception as e:
            logger.error(f"Database symptom analysis failed: {e}")
            await db.rollback()
        # 3) Last resort: the small in-memory knowledge base.
        if not results:
            try:
                results = analyzer.predict(body.symptoms, follow_up)
            except Exception as e:
                logger.error(f"Symptom analysis error: {e}")
                raise HTTPException(status_code=500, detail="Analysis service error. Please try again.")

    enriched = []
    for r in results:
        item = {
            "name":           r.get("name", "Unknown"),
            "icd_code":       r.get("icd_code", ""),
            "probability":    r.get("probability", 0),
            "severity":       r.get("severity", 0),
            "severity_level": r.get("severity_level", "Unknown"),
            "specialist":     r.get("specialist", "General Physician"),
            "precautions":    r.get("precautions", []),
            "home_remedies":  r.get("home_remedies", []),
            "medications":    r.get("medications", []),
            "recommendations": r.get("recommendations", []),
            "description":    r.get("description", ""),
        }
        if r.get("slug"):                       # lets the UI link to /diseases/<slug>
            item["slug"] = r["slug"]
            item["disease_id"] = r.get("disease_id")
        enriched.append(item)

    # Persist (anonymous if not logged in). A failure here must not fail the request.
    try:
        db.add(SymptomCheck(
            user_id=current_user.id if current_user else None,
            symptoms=body.symptoms,
            follow_up=follow_up,
            results=enriched,
            ai_powered=ai_powered,
        ))
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.warning(f"Failed to persist symptom check: {e}")

    return {
        "analyzed_symptoms": body.symptoms,
        "possible_diseases": enriched,
        "ai_powered": ai_powered,
        "disclaimer": (
            "This AI-generated analysis is for informational purposes only and does not "
            "constitute medical advice. Always consult a qualified healthcare professional "
            "for accurate diagnosis and treatment."
        ),
    }


@router.get("/list")
async def list_symptoms(
    q: Optional[str] = Query(None, description="Filter by name (substring)"),
    common_only: bool = False,
    limit: int = Query(2000, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Symptom.id, Symptom.name, Symptom.is_common)
    if common_only:
        stmt = stmt.where(Symptom.is_common.is_(True))
    if q and q.strip():
        stmt = stmt.where(Symptom.name.ilike(f"%{escape_like(q.strip())}%", escape="\\"))
    rows = (await db.execute(
        stmt.order_by(Symptom.is_common.desc(), Symptom.name).limit(limit)
    )).all()

    if not rows and not q and not common_only:
        return {"symptoms": [{"name": s, "is_common": True} for s in analyzer.all_symptoms]}

    return {
        "symptoms": [
            {"id": str(sid), "name": name, "is_common": bool(common)}
            for sid, name, common in rows
        ]
    }


@router.post("/followup")
async def get_followup_questions(body: FollowUpRequest):
    return {"questions": [
        {"id": "duration",  "question": "How long have you had these symptoms?",
         "options": ["Less than 24 hours", "1-3 days", "4-7 days", "More than a week"]},
        {"id": "severity",  "question": "How severe are your symptoms?",
         "options": ["Mild - slightly uncomfortable", "Moderate - affects daily activities",
                     "Severe - very uncomfortable", "Critical - need immediate help"]},
        {"id": "age_group", "question": "What is your age group?",
         "options": ["Under 18", "18-35", "36-60", "Over 60"]},
        {"id": "chronic",   "question": "Do you have any chronic conditions?",
         "options": ["None", "Diabetes", "Hypertension", "Heart disease", "Other"]},
    ]}
