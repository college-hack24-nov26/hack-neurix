import secrets
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.config.settings import settings
from app.middleware.auth import get_current_user, parse_uuid
from app.models.models import (
    LabBooking, LabBookingTest, LabReport, Laboratory, LaboratoryServiceArea,
    LaboratoryTest, Notification, User,
)
from app.utils import iso

router = APIRouter()
ALLOWED_REPORT_TYPES = {"application/pdf", "image/jpeg", "image/png"}
MAX_REPORT_SIZE = settings.MAX_FILE_SIZE_MB * 1024 * 1024


class BookingRequest(BaseModel):
    laboratory_id: str
    test_ids: list[str] = Field(min_length=1)
    patient_name: str = Field(min_length=1, max_length=200)
    patient_phone: str = Field(min_length=7, max_length=30)
    address: str = Field(min_length=1)
    pincode: str = Field(min_length=4, max_length=12)
    landmark: Optional[str] = ""
    preferred_at: datetime
    special_instructions: Optional[str] = ""


@router.get("/nearby")
async def nearby_laboratories(
    area: str = Query(..., min_length=2),
    db: AsyncSession = Depends(get_db),
):
    if not settings.GOOGLE_MAPS_API_KEY:
        raise HTTPException(
            status_code=503,
            detail="Google Maps is not configured. Add GOOGLE_MAPS_API_KEY on the backend.",
        )

    query = f"diagnostic laboratory near {area.strip()}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        response = await client.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={
                "query": query,
                "key": settings.GOOGLE_MAPS_API_KEY,
                "region": "in",
                "language": "en",
            },
        )
        response.raise_for_status()
        payload = response.json()

    if payload.get("status") not in ("OK", "ZERO_RESULTS"):
        raise HTTPException(
            status_code=502,
            detail=f"Google Places lookup failed: {payload.get('error_message', payload.get('status'))}",
        )

    area_label = area.strip()
    result_labs = []
    for place in payload.get("results", [])[:30]:
        location = (place.get("geometry") or {}).get("location") or {}
        address = place.get("formatted_address") or ""
        name = (place.get("name") or "").strip()
        if not name:
            continue

        import re
        pincode_match = re.search(r"\b\d{6}\b", address)
        pincode = pincode_match.group(0) if pincode_match else None
        lab_city = area_label

        lab = await db.scalar(
            select(Laboratory).where(
                func.lower(Laboratory.name) == name.lower(),
                func.lower(func.coalesce(Laboratory.city, "")) == lab_city.lower(),
            )
        )
        if lab is None:
            lab = Laboratory(
                name=name,
                address=address,
                city=lab_city,
                state=None,
                pincode=pincode,
                latitude=location.get("lat"),
                longitude=location.get("lng"),
                rating=place.get("rating"),
                home_collection=True,
                verification_status="pending",
                is_active=True,
            )
            db.add(lab)
            await db.flush()
        else:
            lab.address = address
            lab.latitude = location.get("lat")
            lab.longitude = location.get("lng")
            lab.rating = place.get("rating")
            if pincode:
                lab.pincode = pincode
            lab.home_collection = True

        tests = (await db.execute(
            select(LaboratoryTest).where(
                LaboratoryTest.laboratory_id == lab.id,
                LaboratoryTest.is_active.is_(True),
            )
        )).scalars().all()
        if not tests:
            db.add_all([
                LaboratoryTest(
                    laboratory_id=lab.id, name="Complete Blood Count (CBC)", category="Blood",
                    sample_type="Blood", preparation="No special preparation",
                    turnaround_hours=24, price=499,
                ),
                LaboratoryTest(
                    laboratory_id=lab.id, name="HbA1c", category="Diabetes",
                    sample_type="Blood", preparation="No fasting required",
                    turnaround_hours=24, price=699,
                ),
                LaboratoryTest(
                    laboratory_id=lab.id, name="Vitamin D", category="Vitamins",
                    sample_type="Blood", preparation="No special preparation",
                    turnaround_hours=48, price=999,
                ),
            ])
            await db.flush()
            tests = (await db.execute(
                select(LaboratoryTest).where(
                    LaboratoryTest.laboratory_id == lab.id,
                    LaboratoryTest.is_active.is_(True),
                )
            )).scalars().all()

        if pincode:
            existing_area = await db.scalar(
                select(LaboratoryServiceArea).where(
                    LaboratoryServiceArea.laboratory_id == lab.id,
                    LaboratoryServiceArea.pincode == pincode,
                )
            )
            if existing_area is None:
                db.add(LaboratoryServiceArea(
                    laboratory_id=lab.id,
                    pincode=pincode,
                    home_collection_fee=99,
                ))

        result_labs.append({
            "id": str(lab.id),
            "name": lab.name,
            "address": lab.address,
            "city": lab.city,
            "pincode": lab.pincode,
            "latitude": lab.latitude,
            "longitude": lab.longitude,
            "phone": lab.phone,
            "rating": lab.rating,
            "home_collection": lab.home_collection,
            "verification_status": lab.verification_status,
            "google_place_id": place.get("place_id"),
            "tests": [{
                "id": str(test.id),
                "name": test.name,
                "category": test.category,
                "description": test.description,
                "sample_type": test.sample_type,
                "preparation": test.preparation,
                "turnaround_hours": test.turnaround_hours,
                "price": test.price,
            } for test in tests],
        })

    await db.commit()
    return {"laboratories": result_labs, "area": area_label, "source": "google_places"}


@router.get("/catalogue")
async def catalogue(area: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(Laboratory).where(
        Laboratory.is_active.is_(True),
        Laboratory.verification_status == "verified",
    )
    if area and area.strip():
        search = f"%{area.strip()}%"
        stmt = stmt.where(
            or_(
                func.lower(func.coalesce(Laboratory.city, "")).like(func.lower(search)),
                func.lower(func.coalesce(Laboratory.state, "")).like(func.lower(search)),
                func.lower(func.coalesce(Laboratory.address, "")).like(func.lower(search)),
                func.lower(func.coalesce(Laboratory.pincode, "")).like(func.lower(search)),
                select(LaboratoryServiceArea).where(
                    LaboratoryServiceArea.laboratory_id == Laboratory.id,
                    func.lower(LaboratoryServiceArea.pincode).like(func.lower(search)),
                ).exists(),
            )
        )
    labs = (await db.execute(stmt.order_by(Laboratory.rating.desc()))).scalars().all()
    result = []
    for lab in labs:
        tests = (await db.execute(select(LaboratoryTest).where(
            LaboratoryTest.laboratory_id == lab.id, LaboratoryTest.is_active.is_(True)
        ).order_by(LaboratoryTest.category, LaboratoryTest.name))).scalars().all()
        result.append({
            "id": str(lab.id), "name": lab.name, "address": lab.address, "city": lab.city,
            "pincode": lab.pincode, "phone": lab.phone, "rating": lab.rating,
            "home_collection": lab.home_collection, "verification_status": lab.verification_status,
            "tests": [{
                "id": str(t.id), "name": t.name, "category": t.category, "description": t.description,
                "sample_type": t.sample_type, "preparation": t.preparation,
                "turnaround_hours": t.turnaround_hours, "price": t.price,
            } for t in tests],
        })
    return {"laboratories": result}


@router.post("/book", status_code=status.HTTP_201_CREATED)
async def book_lab(
    body: BookingRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    lab_id = parse_uuid(body.laboratory_id)
    if lab_id is None:
        raise HTTPException(400, "Invalid laboratory ID.")
    lab = await db.get(Laboratory, lab_id)
    if not lab or not lab.is_active:
        raise HTTPException(404, "Laboratory not found.")

    preferred_at = body.preferred_at
    if preferred_at.tzinfo is None:
        preferred_at = preferred_at.replace(tzinfo=timezone.utc)
    else:
        preferred_at = preferred_at.astimezone(timezone.utc)
    minimum_collection_time = datetime.now(timezone.utc) + timedelta(minutes=30)
    if preferred_at < minimum_collection_time:
        raise HTTPException(
            400,
            "Preferred collection time must be at least 30 minutes in the future.",
        )

    test_ids = []
    for raw_id in set(body.test_ids):
        parsed = parse_uuid(raw_id)
        if parsed is not None:
            test_ids.append(parsed)
    tests = (await db.execute(select(LaboratoryTest).where(
        LaboratoryTest.id.in_(test_ids),
        LaboratoryTest.laboratory_id == lab.id,
        LaboratoryTest.is_active.is_(True),
    ))).scalars().all()
    if len(tests) != len(set(test_ids)):
        raise HTTPException(400, "One or more selected tests are invalid.")

    area = await db.scalar(select(LaboratoryServiceArea).where(
        LaboratoryServiceArea.laboratory_id == lab.id,
        LaboratoryServiceArea.pincode == body.pincode,
    ))
    collection_fee = area.home_collection_fee if area else 0
    test_total = sum(t.price for t in tests)
    booking_ref = f"LAB{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}{secrets.token_hex(2).upper()}"
    booking = LabBooking(
        booking_ref=booking_ref, user_id=current_user.id, laboratory_id=lab.id,
        patient_name=body.patient_name.strip(), patient_phone=body.patient_phone.strip(),
        address=body.address.strip(), pincode=body.pincode.strip(), landmark=body.landmark or None,
        preferred_at=preferred_at, special_instructions=body.special_instructions or None,
        test_total=test_total, collection_fee=collection_fee, status="booking_requested",
        status_history=[{"status": "booking_requested", "at": iso(datetime.now(timezone.utc))}],
    )
    db.add(booking)
    await db.flush()
    db.add_all([LabBookingTest(booking_id=booking.id, test_id=t.id, price=t.price) for t in tests])
    db.add(Notification(user_id=current_user.id, title="Laboratory booking received",
                        message=f"Your booking {booking_ref} has been received.", type="lab_booking"))
    await db.commit()
    return booking_summary(booking, lab, tests)


def booking_summary(b: LabBooking, lab: Laboratory, tests: list[LaboratoryTest] | None = None) -> dict:
    return {
        "id": str(b.id), "booking_ref": b.booking_ref, "laboratory": lab.name,
        "patient_name": b.patient_name, "patient_phone": b.patient_phone,
        "preferred_at": iso(b.preferred_at), "status": b.status,
        "test_total": b.test_total, "collection_fee": b.collection_fee,
        "total": b.test_total + b.collection_fee, "status_history": b.status_history,
        "created_at": iso(b.created_at), "tests": [
            {"id": str(t.id), "name": t.name, "price": t.price} for t in (tests or [])
        ],
    }


@router.get("/bookings")
async def my_bookings(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(LabBooking, Laboratory).join(Laboratory, Laboratory.id == LabBooking.laboratory_id)
        .where(LabBooking.user_id == current_user.id).order_by(LabBooking.created_at.desc()).limit(200)
    )).all()
    result = []
    for booking, lab in rows:
        result.append(booking_summary(booking, lab))
    return {"bookings": result}


@router.get("/reports")
async def my_reports(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(LabReport).where(LabReport.user_id == current_user.id)
                             .order_by(LabReport.uploaded_at.desc()).limit(200))).scalars().all()
    return {"reports": [{
        "id": str(r.id), "booking_id": str(r.booking_id), "title": r.title,
        "file_size": r.file_size, "mime_type": r.mime_type, "uploaded_at": iso(r.uploaded_at),
        "ai_analysis": r.ai_analysis,
    } for r in rows]}


@router.post("/bookings/{booking_id}/reports")
async def upload_report(
    booking_id: str,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    bid = parse_uuid(booking_id)
    booking = await db.scalar(select(LabBooking).where(
        LabBooking.id == bid, LabBooking.user_id == current_user.id
    )) if bid else None
    if not booking:
        raise HTTPException(404, "Booking not found.")
    if file.content_type not in ALLOWED_REPORT_TYPES:
        raise HTTPException(400, "Only PDF and JPEG/PNG files are allowed.")
    contents = await file.read()
    if len(contents) > MAX_REPORT_SIZE:
        raise HTTPException(413, f"Maximum report size is {settings.MAX_FILE_SIZE_MB} MB.")

    ext = Path(file.filename).suffix.lower() if file.filename else ".bin"
    user_dir = Path(settings.UPLOAD_DIR) / "lab-reports" / str(current_user.id)
    user_dir.mkdir(parents=True, exist_ok=True)
    dest = user_dir / f"{uuid.uuid4().hex}{ext}"
    dest.write_bytes(contents)
    report = LabReport(
        booking_id=booking.id, user_id=current_user.id, laboratory_id=booking.laboratory_id,
        title=Path(file.filename).name if file.filename else "Lab report",
        file_path=str(dest), mime_type=file.content_type, file_size=len(contents),
    )
    try:
        db.add(report)
        booking.status = "report_uploaded"
        booking.status_history = list(booking.status_history or []) + [{"status": "report_uploaded", "at": iso(datetime.now(timezone.utc))}]
        await db.commit()
    except Exception:
        await db.rollback()
        dest.unlink(missing_ok=True)
        raise
    return {"id": str(report.id), "title": report.title, "uploaded_at": iso(report.uploaded_at)}


@router.get("/reports/{report_id}/download")
async def download_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    rid = parse_uuid(report_id)
    report = await db.scalar(select(LabReport).where(
        LabReport.id == rid, LabReport.user_id == current_user.id
    )) if rid else None
    if not report:
        raise HTTPException(404, "Report not found.")
    path = Path(report.file_path)
    if not path.is_file():
        raise HTTPException(404, "Report file is unavailable.")
    return FileResponse(path, media_type=report.mime_type, filename=report.title)
