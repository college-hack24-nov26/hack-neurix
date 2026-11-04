"""
HomeCare+ — Health Records Routes (PostgreSQL Edition)
POST   /records/upload       — upload a medical record
GET    /records              — list user's records
GET    /records/{id}         — get a specific record
DELETE /records/{id}         — delete a record
POST   /records/{id}/analyze — trigger AI analysis of a record
"""
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import get_current_user, parse_uuid
from app.models.models import RECORD_TYPE_VALUES, HealthRecord, User
from app.utils import iso

router = APIRouter()

ALLOWED_TYPES = {
    "application/pdf", "image/jpeg", "image/png",
    "image/webp", "image/bmp",
}
MAX_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024   # bytes


def record_to_dict(r: HealthRecord) -> dict:
    return {
        "id":           str(r.id),
        "name":         r.name,
        "record_type":  r.record_type,
        "file_path":    r.file_path,
        "file_size":    r.file_size,
        "mime_type":    r.mime_type,
        "tags":         list(r.tags or []),
        "is_analyzed":  r.is_analyzed,
        "ai_analysis":  r.ai_analysis,
        "uploaded_at":  iso(r.uploaded_at),
    }


async def _get_owned_record(db: AsyncSession, record_id: str, user: User) -> HealthRecord:
    rid = parse_uuid(record_id)
    record = None
    if rid is not None:
        record = await db.scalar(
            select(HealthRecord).where(HealthRecord.id == rid, HealthRecord.user_id == user.id)
        )
    if not record:
        raise HTTPException(status_code=404, detail="Record not found.")
    return record


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_record(
    file:        UploadFile = File(...),
    name:        str        = Form(...),
    record_type: str        = Form("document"),
    tags:        str        = Form(""),          # comma-separated
    current_user: User      = Depends(get_current_user),
    db: AsyncSession        = Depends(get_db),
):
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"File type '{file.content_type}' not allowed. Use PDF or image files."
        )
    if record_type not in RECORD_TYPE_VALUES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid record type. Use one of: {', '.join(RECORD_TYPE_VALUES)}."
        )

    contents = await file.read()
    if len(contents) > MAX_SIZE:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE_MB} MB."
        )

    ext      = Path(file.filename).suffix.lower() if file.filename else ".bin"
    filename = f"{uuid.uuid4().hex}{ext}"
    user_dir = Path(settings.UPLOAD_DIR) / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest     = user_dir / filename
    dest.write_bytes(contents)

    record = HealthRecord(
        user_id=current_user.id,
        name=name,
        record_type=record_type,
        file_path=str(dest),
        file_size=len(contents),
        mime_type=file.content_type,
        tags=[t.strip() for t in tags.split(",") if t.strip()],
    )
    try:
        db.add(record)
        await db.commit()
    except Exception:
        await db.rollback()
        dest.unlink(missing_ok=True)        # don't leave an orphan file behind
        raise
    return record_to_dict(record)


@router.get("")
async def list_records(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    records = (await db.execute(
        select(HealthRecord).where(HealthRecord.user_id == current_user.id)
        .order_by(HealthRecord.uploaded_at.desc()).limit(1000)
    )).scalars().all()
    return {"records": [record_to_dict(r) for r in records]}


@router.get("/{record_id}")
async def get_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return record_to_dict(await _get_owned_record(db, record_id, current_user))


@router.delete("/{record_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    record = await _get_owned_record(db, record_id, current_user)
    file_path = record.file_path

    await db.delete(record)
    await db.commit()

    # remove the file only after the row is gone
    if file_path and Path(file_path).exists():
        Path(file_path).unlink(missing_ok=True)


@router.post("/{record_id}/analyze")
async def analyze_record(
    record_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Trigger AI analysis of an uploaded record (image/PDF)."""
    record = await _get_owned_record(db, record_id, current_user)

    from app.services.analysis_service import AnalysisService, AnalysisError
    try:
        result = await AnalysisService().analyze_file(record.file_path, record.mime_type)
    except AnalysisError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)

    record.ai_analysis = result
    record.is_analyzed = True
    await db.commit()
    return record_to_dict(record)
