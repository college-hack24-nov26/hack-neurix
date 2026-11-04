"""
HomeCare+ — idempotent PostgreSQL seeding.

Everything here is safe to run repeatedly and from several processes at once
(a Postgres advisory lock serialises runs, every insert is ON CONFLICT DO NOTHING).

What gets loaded
  * 18 organ systems and ~347 unique diseases from app/data/disease_dataset.py
    (13 diseases the dataset lists under two organ systems are merged into one row)
  * ~940 symptoms, extracted from the dataset, linked to diseases through
    `disease_symptoms` with an IDF weight (rare symptoms count for more)
  * treatment info (precautions, home remedies, medications, severity score,
    specialist) merged in from the 57-disease knowledge base that used to live
    only inside the symptom checker
  * sample hospitals, telemedicine doctors and (outside production) a demo user
"""
from __future__ import annotations

import logging
import re
from typing import Dict, Iterable, List, Optional, Tuple

from sqlalchemy import select, text, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.settings import settings
from app.data.disease_dataset import DISEASES_BY_SYSTEM, ORGAN_SYSTEMS
from app.models.models import (
    SEVERITY_SCORE, Disease, DiseaseSymptom, Doctor, Hospital, OrganSystem,
    Symptom, User,
)

logger = logging.getLogger(__name__)

SEED_LOCK_ID = 727_001          # arbitrary app-wide advisory lock key
_SEVERITY_RANK = {"Mild": 0, "Moderate": 1, "Severe": 2, "Critical": 3}

# Symptoms shown as quick-pick chips (union of what the old Mongo seeders and the UI used).
COMMON_SYMPTOMS = [
    "Fever", "Headache", "Cough", "Fatigue", "Nausea", "Vomiting", "Chest Pain",
    "Shortness of Breath", "Dizziness", "Sore Throat", "Body Aches", "Runny Nose",
    "Diarrhea", "Abdominal Pain", "Back Pain", "Joint Pain", "Skin Rash",
    "Loss of Appetite", "Chills", "Sweating", "Swelling", "Numbness",
    "Blurred Vision", "Ear Pain", "Toothache", "Muscle Pain", "Weight Loss",
    "Tingling", "Constipation", "Insomnia", "Anxiety", "Palpitations", "Rash",
]
# Additional display names that are NOT quick-pick chips
OTHER_SYMPTOMS = [
    "Wheezing", "Heartburn", "Frequent Urination", "Excessive Thirst",
]

SAMPLE_HOSPITALS = [
    {"name": "City Medical Center",  "type": "hospital", "city": "Pune", "state": "Maharashtra", "phone": "+91-20-1234-5678", "latitude": 18.5204, "longitude": 73.8567, "specialties": ["Cardiology", "Neurology", "Orthopedics", "General Medicine"], "rating": 4.5},
    {"name": "Apollo Hospital Pune", "type": "hospital", "city": "Pune", "state": "Maharashtra", "phone": "+91-20-2345-6789", "latitude": 18.5122, "longitude": 73.8456, "specialties": ["Oncology", "Cardiac Surgery", "Neurosurgery"], "rating": 4.8},
    {"name": "Ruby Hall Clinic",     "type": "hospital", "city": "Pune", "state": "Maharashtra", "phone": "+91-20-3456-7890", "latitude": 18.5308, "longitude": 73.8741, "specialties": ["Multi-specialty", "Emergency Care", "ICU"], "rating": 4.6},
    {"name": "Green Valley Clinic",  "type": "clinic",   "city": "Pune", "state": "Maharashtra", "phone": "+91-20-4567-8901", "latitude": 18.5180, "longitude": 73.8540, "specialties": ["General Medicine", "Pediatrics", "Dermatology"], "rating": 4.3},
    {"name": "MedPlus Pharmacy",     "type": "pharmacy", "city": "Pune", "state": "Maharashtra", "phone": "+91-20-5678-9012", "latitude": 18.5190, "longitude": 73.8550, "specialties": ["Pharmacy", "Health Products"], "rating": 4.2},
    {"name": "Smile Dental Clinic",  "type": "dental",   "city": "Pune", "state": "Maharashtra", "phone": "+91-20-6789-0123", "latitude": 18.5240, "longitude": 73.8620, "specialties": ["Dentistry", "Orthodontics", "Oral Surgery"], "rating": 4.6},
]

SAMPLE_DOCTORS = [
    {"name": "Dr. Priya Sharma",  "specialization": "General Physician",  "hospital": "Apollo Hospitals",            "experience": 12, "rating": 4.9, "fee": 500,  "languages": ["English", "Hindi", "Marathi"], "status": "available"},
    {"name": "Dr. Rahul Mehta",   "specialization": "Cardiologist",       "hospital": "Fortis Hospital",             "experience": 18, "rating": 4.8, "fee": 1200, "languages": ["English", "Hindi"],            "status": "available"},
    {"name": "Dr. Anjali Nair",   "specialization": "Dermatologist",      "hospital": "Manipal Hospital",            "experience": 9,  "rating": 4.7, "fee": 800,  "languages": ["English", "Malayalam"],        "status": "available"},
    {"name": "Dr. Vikram Rajan",  "specialization": "Neurologist",        "hospital": "NIMHANS",                     "experience": 15, "rating": 4.9, "fee": 1500, "languages": ["English", "Kannada"],          "status": "busy"},
    {"name": "Dr. Fatima Khan",   "specialization": "Gynecologist",       "hospital": "Lilavati Hospital",           "experience": 14, "rating": 4.8, "fee": 900,  "languages": ["English", "Hindi", "Urdu"],    "status": "available"},
    {"name": "Dr. Suresh Patil",  "specialization": "Orthopedic Surgeon", "hospital": "Kokilaben Hospital",          "experience": 20, "rating": 4.7, "fee": 1100, "languages": ["English", "Marathi"],          "status": "available"},
    {"name": "Dr. Meera Krishnan","specialization": "Pediatrician",       "hospital": "Rainbow Children's Hospital", "experience": 11, "rating": 4.9, "fee": 700,  "languages": ["English", "Tamil"],            "status": "available"},
    {"name": "Dr. Arun Gupta",    "specialization": "Psychiatrist",       "hospital": "NIMHANS",                     "experience": 13, "rating": 4.8, "fee": 1000, "languages": ["English", "Hindi"],            "status": "offline"},
]


# ── helpers ──────────────────────────────────────────────────────────────────
def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def clean_symptom(value: str) -> str:
    return " ".join(value.strip().split())


def display_name(value: str) -> str:
    """'chest pain' -> 'Chest pain' (keeps the rest of the casing untouched)."""
    value = clean_symptom(value)
    return value[:1].upper() + value[1:]


async def _acquire_lock(session: AsyncSession) -> None:
    await session.execute(text("SELECT pg_advisory_xact_lock(:k)"), {"k": SEED_LOCK_ID})


# ── dataset preparation (pure python, unit-testable) ─────────────────────────
def build_disease_records() -> List[dict]:
    """
    Flatten DISEASES_BY_SYSTEM into one record per unique disease:
      * duplicates (same name in two organ systems) are merged: symptoms are
        unioned, the higher severity wins, the first organ system is primary
      * the symptom-checker knowledge base is overlaid (precautions, home
        remedies, medications, severity score, specialist, extra symptoms)
    """
    from app.services.symptom_service import DISEASE_KB       # local import: avoids cycles

    organ_by_slug = {o["slug"]: o for o in ORGAN_SYSTEMS}
    merged: Dict[str, dict] = {}
    order: List[str] = []

    for organ_slug, rows in DISEASES_BY_SYSTEM.items():
        organ = organ_by_slug[organ_slug]
        for name, icd, symptoms, overview, severity in rows:
            key = name.strip().lower()
            syms = [clean_symptom(s) for s in symptoms if s and s.strip()]
            if key in merged:
                rec = merged[key]
                seen = {s.lower() for s in rec["symptoms"]}
                rec["symptoms"] += [s for s in syms if s.lower() not in seen]
                if _SEVERITY_RANK.get(severity, 0) > _SEVERITY_RANK.get(rec["severity"], 0):
                    rec["severity"] = severity
                continue
            merged[key] = {
                "name": name.strip(), "icd_code": icd, "organ_slug": organ_slug,
                "category": organ["name"], "severity": severity, "overview": overview,
                "symptoms": syms, "specialist": organ["specialist"],
                "severity_score": SEVERITY_SCORE.get(severity, 55),
                "precautions": [], "home_remedies": [], "medications": [],
            }
            order.append(key)

    # Overlay the knowledge base: by exact name first, then by unique ICD code.
    by_icd: Dict[str, List[str]] = {}
    for key in order:
        by_icd.setdefault(merged[key]["icd_code"], []).append(key)

    for kb in DISEASE_KB:
        key = kb["name"].strip().lower()
        if key not in merged:
            candidates = by_icd.get(kb["icd"], [])
            if len(candidates) != 1:
                logger.warning("Knowledge-base disease %r has no match in the dataset", kb["name"])
                continue
            key = candidates[0]
        rec = merged[key]
        rec["precautions"] = list(kb.get("precautions", []))
        rec["home_remedies"] = list(kb.get("home_remedies", []))
        rec["medications"] = list(kb.get("medications", []))
        rec["severity_score"] = kb.get("severity_score", rec["severity_score"])
        rec["specialist"] = kb.get("specialist", rec["specialist"])
        seen = {s.lower() for s in rec["symptoms"]}
        rec["symptoms"] += [clean_symptom(s) for s in kb.get("symptoms", []) if s.lower() not in seen
                            and not seen.add(s.lower())]

    # Unique, deterministic slugs
    used: set = set()
    records = []
    for key in order:
        rec = merged[key]
        slug = slugify(rec["name"])
        if slug in used:
            slug = f"{slug}-{slugify(rec['icd_code'])}"
        n = 2
        base = slug
        while slug in used:
            slug = f"{base}-{n}"
            n += 1
        used.add(slug)
        rec["slug"] = slug
        records.append(rec)
    return records


# ── seeding steps ────────────────────────────────────────────────────────────
async def seed_organ_systems(session: AsyncSession) -> Dict[str, int]:
    stmt = pg_insert(OrganSystem).values(ORGAN_SYSTEMS).on_conflict_do_nothing(index_elements=["slug"])
    await session.execute(stmt)
    rows = (await session.execute(select(OrganSystem.slug, OrganSystem.id))).all()
    return {slug: id_ for slug, id_ in rows}


async def seed_symptoms(session: AsyncSession, names: Iterable[str]) -> Dict[str, int]:
    """Insert every symptom name (dedup by slug) and return slug -> id."""
    curated = {slugify(n): n for n in COMMON_SYMPTOMS + OTHER_SYMPTOMS}
    common_slugs = {slugify(n) for n in COMMON_SYMPTOMS}

    wanted: Dict[str, str] = {}
    for n in list(curated.values()) + list(names):
        n = clean_symptom(n)
        if not n:
            continue
        slug = slugify(n)
        if not slug:
            continue
        wanted.setdefault(slug, curated.get(slug) or display_name(n))

    values = [{"name": name, "slug": slug, "is_common": slug in common_slugs}
              for slug, name in wanted.items()]
    for i in range(0, len(values), 1000):
        await session.execute(
            pg_insert(Symptom).values(values[i:i + 1000]).on_conflict_do_nothing(index_elements=["slug"])
        )
    # make sure chips flagged common stay common even if the row pre-existed
    await session.execute(update(Symptom).where(Symptom.slug.in_(common_slugs)).values(is_common=True))
    rows = (await session.execute(select(Symptom.slug, Symptom.id))).all()
    return {slug: id_ for slug, id_ in rows}


async def seed_diseases(session: AsyncSession) -> Tuple[int, int]:
    """Returns (diseases_in_dataset, links_in_db)."""
    organ_ids = await seed_organ_systems(session)
    records = build_disease_records()
    symptom_ids = await seed_symptoms(session, (s for r in records for s in r["symptoms"]))

    rows = []
    for r in records:
        rows.append({
            "name": r["name"], "slug": r["slug"], "icd_code": r["icd_code"],
            "organ_system_id": organ_ids[r["organ_slug"]], "category": r["category"],
            "severity": r["severity"], "severity_score": r["severity_score"],
            "overview": r["overview"], "specialist": r["specialist"],
            "specialist_type": r["specialist"], "is_dental": False,
            "precautions": r["precautions"], "home_remedies": r["home_remedies"],
            "medications": r["medications"],
        })
    for i in range(0, len(rows), 200):
        await session.execute(
            pg_insert(Disease).values(rows[i:i + 200]).on_conflict_do_nothing(index_elements=["slug"])
        )
    disease_ids = {slug: id_ for slug, id_ in (await session.execute(select(Disease.slug, Disease.id))).all()}

    # Existing rows (e.g. imported from MongoDB) keep their data, but any EMPTY
    # treatment lists / missing score get filled from the dataset.
    for r in records:
        did = disease_ids[r["slug"]]
        await session.execute(
            update(Disease).where(Disease.id == did).values(
                precautions=text("CASE WHEN cardinality(precautions) = 0 THEN CAST(:p AS text[]) ELSE precautions END")
                .bindparams(p=r["precautions"]),
                home_remedies=text("CASE WHEN cardinality(home_remedies) = 0 THEN CAST(:h AS text[]) ELSE home_remedies END")
                .bindparams(h=r["home_remedies"]),
                medications=text("CASE WHEN cardinality(medications) = 0 THEN CAST(:m AS text[]) ELSE medications END")
                .bindparams(m=r["medications"]),
                severity_score=text("COALESCE(severity_score, :s)").bindparams(s=r["severity_score"]),
            )
        )

    links = []
    for r in records:
        did = disease_ids[r["slug"]]
        seen = set()
        for pos, s in enumerate(r["symptoms"]):
            sid = symptom_ids[slugify(s)]
            if sid in seen:
                continue
            seen.add(sid)
            links.append({"disease_id": did, "symptom_id": sid, "position": pos})
    for i in range(0, len(links), 2000):
        await session.execute(
            pg_insert(DiseaseSymptom).values(links[i:i + 2000])
            .on_conflict_do_nothing(index_elements=["disease_id", "symptom_id"])
        )
    await recompute_symptom_weights(session)
    total_links = (await session.execute(text("SELECT count(*) FROM disease_symptoms"))).scalar_one()
    return len(records), total_links


async def recompute_symptom_weights(session: AsyncSession) -> None:
    """
    IDF weighting:  weight(symptom) = max(0.25, ln(N_diseases / diseases_with_symptom)).
    'fever' (in dozens of diseases) ends up near the floor, 'Koplik spots' near the max.
    Run again whenever diseases/symptom links are added in bulk.
    """
    await session.execute(text("""
        UPDATE disease_symptoms ds
           SET weight = GREATEST(0.25, LN((SELECT count(*) FROM diseases)::float / s.df))
          FROM (SELECT symptom_id, count(*)::float AS df
                  FROM disease_symptoms GROUP BY symptom_id) s
         WHERE ds.symptom_id = s.symptom_id
    """))


async def seed_hospitals(session: AsyncSession) -> None:
    await session.execute(
        pg_insert(Hospital).values(SAMPLE_HOSPITALS).on_conflict_do_nothing(constraint="uq_hospitals_name_city")
    )


async def seed_doctors(session: AsyncSession) -> None:
    await session.execute(pg_insert(Doctor).values(SAMPLE_DOCTORS).on_conflict_do_nothing(index_elements=["name"]))


async def seed_demo_user(session: AsyncSession) -> bool:
    """Creates demo@homecare.plus / Demo@1234 — never in production."""
    if settings.APP_ENV.lower() == "production":
        return False
    from app.middleware.auth import hash_password
    exists = (await session.execute(
        text("SELECT 1 FROM users WHERE lower(email) = 'demo@homecare.plus'"))).first()
    if exists:
        return False
    session.add(User(
        first_name="Demo", last_name="User", email="demo@homecare.plus",
        password_hash=hash_password("Demo@1234"), language="en", is_active=True, is_verified=True,
    ))
    return True


async def seed_all(session: AsyncSession) -> dict:
    """Run every seeder inside the caller's transaction (caller commits)."""
    await _acquire_lock(session)
    n_diseases, n_links = await seed_diseases(session)
    await seed_hospitals(session)
    await seed_doctors(session)
    demo = await seed_demo_user(session)
    counts = {
        "organ_systems": (await session.execute(text("SELECT count(*) FROM organ_systems"))).scalar_one(),
        "diseases": (await session.execute(text("SELECT count(*) FROM diseases"))).scalar_one(),
        "symptoms": (await session.execute(text("SELECT count(*) FROM symptoms"))).scalar_one(),
        "disease_symptom_links": n_links,
        "hospitals": (await session.execute(text("SELECT count(*) FROM hospitals"))).scalar_one(),
        "doctors": (await session.execute(text("SELECT count(*) FROM doctors"))).scalar_one(),
        "demo_user_created": demo,
    }
    return counts
