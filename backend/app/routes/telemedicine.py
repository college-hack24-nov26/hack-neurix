"""
HomeCare+ — Telemedicine Routes (PostgreSQL Edition)
GET  /telemedicine/doctors          — list doctors
POST /telemedicine/book             — book a consultation (persisted)
GET  /telemedicine/consultations    — the user's consultations
"""
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import get_current_user
from app.models.models import Consultation, ConsultationPrescription, Doctor, User
from app.utils import iso

router = APIRouter()


class BookingRequest(BaseModel):
    doctor_id:    int
    slot:         str = Field(min_length=1, max_length=60)
    consult_type: str = Field("video", pattern="^(video|chat|audio)$")
    reason:       Optional[str] = ""


def doctor_dict(d: Doctor) -> dict:
    return {
        "id": d.id, "name": d.name, "specialization": d.specialization,
        "hospital": d.hospital, "experience": d.experience, "rating": d.rating,
        "fee": d.fee, "languages": list(d.languages or []), "status": d.status,
    }


@router.get("/doctors")
async def list_doctors(specialization: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Doctor).order_by(Doctor.id)
    if specialization and specialization.lower() != "all":
        stmt = stmt.where(func.lower(Doctor.specialization) == specialization.lower())
    return {"doctors": [doctor_dict(d) for d in (await db.execute(stmt)).scalars().all()]}


@router.post("/book")
async def book_consultation(
    body: BookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    doctor = await db.get(Doctor, body.doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found.")
    if doctor.status == "offline":
        raise HTTPException(status_code=400, detail="Doctor is currently offline.")

    booking_ref = f"BK{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
    db.add(Consultation(
        booking_ref=booking_ref, user_id=current_user.id, doctor_id=doctor.id,
        slot=body.slot, consult_type=body.consult_type, reason=body.reason or None,
        fee=doctor.fee, status="confirmed",
    ))
    await db.commit()

    return {
        "booking_id":     booking_ref,
        "doctor":         doctor.name,
        "specialization": doctor.specialization,
        "slot":           body.slot,
        "type":           body.consult_type,
        "fee":            doctor.fee,
        "status":         "confirmed",
        "message":        f"Consultation booked with {doctor.name} at {body.slot}.",
    }


@router.get("/consultations")
async def my_consultations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rows = (await db.execute(
        select(Consultation, Doctor).join(Doctor, Doctor.id == Consultation.doctor_id)
        .where(Consultation.user_id == current_user.id)
        .order_by(Consultation.created_at.desc()).limit(200)
    )).all()
    result = []
    for c, d in rows:
        prescription = await db.scalar(select(ConsultationPrescription).where(
            ConsultationPrescription.consultation_id == c.id
        ))
        result.append({
            "booking_id": c.booking_ref, "doctor": d.name, "specialization": d.specialization,
            "slot": c.slot, "type": c.consult_type, "reason": c.reason, "fee": c.fee,
            "status": c.status, "created_at": iso(c.created_at),
            "prescription": None if not prescription else {
                "id": str(prescription.id),
                "title": prescription.title,
                "file_size": prescription.file_size,
                "uploaded_at": iso(prescription.uploaded_at),
            },
        })
    return {"consultations": result}


@router.post("/consultations/{booking_id}/prescription")
async def upload_prescription(
    booking_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consultation = await db.scalar(select(Consultation).where(
        Consultation.booking_ref == booking_id,
        Consultation.user_id == current_user.id,
    ))
    if not consultation:
        raise HTTPException(404, "Consultation not found.")
    if file.content_type != "application/pdf":
        raise HTTPException(400, "Prescription must be a PDF file.")

    contents = await file.read()
    max_size = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if len(contents) > max_size:
        raise HTTPException(413, f"Maximum prescription size is {settings.MAX_FILE_SIZE_MB} MB.")

    user_dir = Path(settings.UPLOAD_DIR) / "prescriptions" / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    destination = user_dir / f"{secrets.token_hex(16)}.pdf"
    destination.write_bytes(contents)

    existing = await db.scalar(select(ConsultationPrescription).where(
        ConsultationPrescription.consultation_id == consultation.id
    ))
    if existing:
        old_path = Path(existing.file_path)
        existing.title = Path(file.filename or "prescription.pdf").name
        existing.file_path = str(destination)
        existing.mime_type = "application/pdf"
        existing.file_size = len(contents)
        existing.uploaded_at = datetime.now(timezone.utc)
        try:
            await db.commit()
        except Exception:
            await db.rollback()
            destination.unlink(missing_ok=True)
            raise
        old_path.unlink(missing_ok=True)
        return {"id": str(existing.id), "title": existing.title, "uploaded_at": iso(existing.uploaded_at)}

    prescription = ConsultationPrescription(
        consultation_id=consultation.id,
        uploaded_by=current_user.id,
        title=Path(file.filename or "prescription.pdf").name,
        file_path=str(destination),
        mime_type="application/pdf",
        file_size=len(contents),
    )
    try:
        db.add(prescription)
        await db.commit()
    except Exception:
        await db.rollback()
        destination.unlink(missing_ok=True)
        raise
    return {"id": str(prescription.id), "title": prescription.title, "uploaded_at": iso(prescription.uploaded_at)}


@router.get("/consultations/{booking_id}/prescription/download")
async def download_prescription(
    booking_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    consultation = await db.scalar(select(Consultation).where(
        Consultation.booking_ref == booking_id,
        Consultation.user_id == current_user.id,
    ))
    if not consultation:
        raise HTTPException(404, "Consultation not found.")
    prescription = await db.scalar(select(ConsultationPrescription).where(
        ConsultationPrescription.consultation_id == consultation.id
    ))
    if not prescription:
        raise HTTPException(404, "Prescription not available yet.")
    path = Path(prescription.file_path)
    if not path.is_file():
        raise HTTPException(404, "Prescription file is unavailable.")
    return FileResponse(path, media_type="application/pdf", filename=prescription.title)
