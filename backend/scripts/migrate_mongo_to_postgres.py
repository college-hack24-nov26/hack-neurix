"""
One-off data migration: MongoDB (old HomeCare+ backend) -> PostgreSQL (new backend).

    pip install -r requirements-migration.txt
    alembic upgrade head                       # the target schema must exist
    python -m scripts.migrate_mongo_to_postgres \
        --mongo-uri mongodb://localhost:27017 --mongo-db homecare_plus --dry-run
    python -m scripts.migrate_mongo_to_postgres \
        --mongo-uri mongodb://localhost:27017 --mongo-db homecare_plus

What it does
  * copies every collection (users, diseases, symptoms, organ systems, symptom checks,
    health metrics/records, chat sessions/messages, hospitals, insurance policies)
  * turns Mongo ObjectId references into real foreign keys
  * keeps password hashes (argon2) -> users sign in with the same passwords
  * keeps created_at / recorded_at / uploaded_at timestamps
  * turns each disease's `symptoms: [..]` array into rows of disease_symptoms
  * skips (and reports) rows that would violate the new constraints, instead of failing
  * runs in ONE transaction: any error rolls everything back; --dry-run always rolls back
  * safe to re-run: existing rows (same email / slug / policy number …) are skipped

Things to know
  * Old JWT tokens (which carried a Mongo ObjectId) stop working: users simply sign in again.
  * The 15 organ systems created by the old `seed_db.py` that have no diseases are not
    copied (the old double-seeding left them empty); pass --keep-empty-organs to copy them.
  * Uploaded files are not touched — `file_path` values are copied as-is, so keep the same
    uploads directory (or move the files and update file_path).
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import os
import re
import sys
import uuid
from collections import Counter, defaultdict
from datetime import date, datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func, select                              # noqa: E402
from sqlalchemy.dialects.postgresql import insert as pg_insert   # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession                  # noqa: E402

from app.models.models import (                                  # noqa: E402
    GENDER_VALUES, METRIC_TYPE_VALUES, RECORD_TYPE_VALUES, SEVERITY_VALUES, SEVERITY_SCORE,
    ChatMessage, ChatSession, Disease, DiseaseSymptom, HealthMetric, HealthRecord, Hospital,
    InsurancePolicy, OrganSystem, Symptom, SymptomCheck, User,
)
from app.seeding import clean_symptom, display_name, recompute_symptom_weights, slugify  # noqa: E402

log = logging.getLogger("migrate")
CHUNK = 1000


# ── value converters ─────────────────────────────────────────────────────────
def to_dt(value: Any, default_now: bool = True) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str) and value.strip():
        try:
            dt = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
            return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
        except ValueError:
            pass
    return datetime.now(timezone.utc) if default_now else None


def to_date(value: Any) -> Optional[date]:
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value.strip():
        try:
            return date.fromisoformat(value.strip()[:10])
        except ValueError:
            return None
    return None


def as_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    return [str(v) for v in value if v is not None and str(v).strip()]


def sid(value: Any) -> Optional[str]:
    return None if value is None else str(value)


def chunks(rows: List[dict], n: int = CHUNK) -> Iterable[List[dict]]:
    for i in range(0, len(rows), n):
        yield rows[i:i + n]


class Report:
    def __init__(self) -> None:
        self.read: Counter = Counter()
        self.written: Counter = Counter()
        self.skipped: Dict[str, List[str]] = defaultdict(list)

    def skip(self, kind: str, reason: str) -> None:
        self.skipped[kind].append(reason)

    def print(self) -> None:
        print("\n{:<22}{:>8}{:>10}{:>9}".format("collection", "read", "written", "skipped"))
        print("-" * 49)
        for kind in sorted(set(self.read) | set(self.written)):
            print("{:<22}{:>8}{:>10}{:>9}".format(
                kind, self.read[kind], self.written[kind], len(self.skipped.get(kind, []))))
        for kind, reasons in self.skipped.items():
            if reasons:
                print(f"\nSkipped {kind}:")
                for reason, n in Counter(reasons).most_common(10):
                    print(f"  {n:>5} × {reason}")


# ── the migration ────────────────────────────────────────────────────────────
async def migrate(mongo_db, session: AsyncSession, keep_empty_organs: bool = False) -> Report:
    rep = Report()

    # 1 ── organ systems ------------------------------------------------------
    organs = list(mongo_db["organ_systems"].find())
    rep.read["organ_systems"] = len(organs)
    used_organ_ids = {sid(d.get("organ_system_id")) for d in mongo_db["diseases"].find({}, {"organ_system_id": 1})}
    organ_map: Dict[str, int] = {}
    for o in organs:
        slug = o.get("slug") or slugify(o.get("name", ""))
        if not slug or not o.get("name"):
            rep.skip("organ_systems", "missing name/slug")
            continue
        if not keep_empty_organs and sid(o["_id"]) not in used_organ_ids:
            rep.skip("organ_systems", "no diseases reference it (old double-seeding leftover)")
            continue
        await session.execute(pg_insert(OrganSystem).values(
            name=o["name"], slug=slug, icon=o.get("icon"), description=o.get("description"),
            specialist=o.get("specialist"),
        ).on_conflict_do_nothing())
        pg_id = await session.scalar(select(OrganSystem.id).where(OrganSystem.slug == slug))
        if pg_id is None:      # name collision with another slug
            pg_id = await session.scalar(select(OrganSystem.id).where(OrganSystem.name == o["name"]))
        if pg_id is None:
            rep.skip("organ_systems", "could not insert")
            continue
        organ_map[sid(o["_id"])] = pg_id
        rep.written["organ_systems"] += 1

    # 2 ── symptoms (catalogue) -----------------------------------------------
    symptom_docs = list(mongo_db["symptoms"].find())
    rep.read["symptoms"] = len(symptom_docs)
    symptom_rows: Dict[str, dict] = {}
    for s in symptom_docs:
        name = clean_symptom(s.get("name", ""))
        slug = slugify(name)
        if not slug:
            rep.skip("symptoms", "empty name")
            continue
        symptom_rows.setdefault(slug, {
            "name": name, "slug": slug, "description": s.get("description"),
            "body_part": s.get("body_part"), "is_common": bool(s.get("is_common", False)),
            "created_at": to_dt(s.get("created_at")),
        })
    for batch in chunks(list(symptom_rows.values())):
        await session.execute(pg_insert(Symptom).values(batch).on_conflict_do_nothing(index_elements=["slug"]))
    rep.written["symptoms"] = len(symptom_rows)

    # 3 ── diseases + disease_symptoms ----------------------------------------
    disease_docs = list(mongo_db["diseases"].find())
    rep.read["diseases"] = len(disease_docs)
    disease_rows: List[dict] = []
    disease_symptoms: Dict[str, List[str]] = {}
    seen_slugs: set = set()
    for d in disease_docs:
        name = (d.get("name") or "").strip()
        slug = d.get("slug") or slugify(name)
        if not name or not slug:
            rep.skip("diseases", "missing name/slug")
            continue
        if slug in seen_slugs:
            rep.skip("diseases", "duplicate slug")
            continue
        seen_slugs.add(slug)
        severity = d.get("severity")
        if severity not in SEVERITY_VALUES:
            severity = str(severity).capitalize() if str(severity).capitalize() in SEVERITY_VALUES else None
        disease_rows.append({
            "name": name, "slug": slug, "icd_code": d.get("icd_code"),
            "organ_system_id": organ_map.get(sid(d.get("organ_system_id"))),
            "category": d.get("category"), "severity": severity,
            "severity_score": SEVERITY_SCORE.get(severity),
            "overview": d.get("overview"),
            "causes": as_list(d.get("causes")), "risk_factors": as_list(d.get("risk_factors")),
            "complications": as_list(d.get("complications")), "treatments": as_list(d.get("treatments")),
            "medications": as_list(d.get("medications")), "home_remedies": as_list(d.get("home_remedies")),
            "prevention": as_list(d.get("prevention")), "precautions": as_list(d.get("precautions")),
            "specialist": d.get("specialist"), "specialist_type": d.get("specialist_type"),
            "is_dental": bool(d.get("is_dental", False)),
            "created_at": to_dt(d.get("created_at")),
        })
        disease_symptoms[slug] = [clean_symptom(s) for s in as_list(d.get("symptoms")) if clean_symptom(s)]
    for batch in chunks(disease_rows, 200):
        await session.execute(pg_insert(Disease).values(batch).on_conflict_do_nothing(index_elements=["slug"]))
    rep.written["diseases"] = len(disease_rows)

    # symptoms mentioned only inside disease documents become catalogue rows too
    extra = {}
    for names in disease_symptoms.values():
        for n in names:
            slug = slugify(n)
            if slug and slug not in symptom_rows:
                extra.setdefault(slug, {"name": display_name(n), "slug": slug, "is_common": False})
    for batch in chunks(list(extra.values())):
        await session.execute(pg_insert(Symptom).values(batch).on_conflict_do_nothing(index_elements=["slug"]))
    sym_ids = {s: i for s, i in (await session.execute(select(Symptom.slug, Symptom.id))).all()}
    dis_ids = {s: i for s, i in (await session.execute(select(Disease.slug, Disease.id))).all()}
    links: List[dict] = []
    for slug, names in disease_symptoms.items():
        seen = set()
        for pos, n in enumerate(names):
            sym_id = sym_ids.get(slugify(n))
            if sym_id and sym_id not in seen and slug in dis_ids:
                seen.add(sym_id)
                links.append({"disease_id": dis_ids[slug], "symptom_id": sym_id, "position": pos})
    for batch in chunks(links, 2000):
        await session.execute(
            pg_insert(DiseaseSymptom).values(batch).on_conflict_do_nothing(index_elements=["disease_id", "symptom_id"]))
    rep.written["disease_symptoms"] = len(links)
    await recompute_symptom_weights(session)

    # 4 ── users ---------------------------------------------------------------
    user_docs = list(mongo_db["users"].find())
    rep.read["users"] = len(user_docs)
    user_map: Dict[str, uuid.UUID] = {}
    for u in user_docs:
        email = (u.get("email") or "").strip().lower()
        if not email or not u.get("password_hash"):
            rep.skip("users", "missing email or password_hash")
            continue
        existing = await session.scalar(select(User.id).where(func.lower(User.email) == email))
        if existing:
            user_map[sid(u["_id"])] = existing        # re-run: reuse, so child rows can still attach
            rep.skip("users", "email already exists in PostgreSQL")
            continue
        gender = (u.get("gender") or "").strip().lower() or None
        new_id = uuid.uuid4()
        session.add(User(
            id=new_id, first_name=u.get("first_name") or "", last_name=u.get("last_name") or "",
            email=email, phone=u.get("phone") or None, password_hash=u["password_hash"],
            date_of_birth=to_date(u.get("date_of_birth")),
            gender=gender if gender in GENDER_VALUES else None,
            profile_photo=u.get("profile_photo"), language=u.get("language") or "en",
            is_active=bool(u.get("is_active", True)), is_verified=bool(u.get("is_verified", False)),
            created_at=to_dt(u.get("created_at")), updated_at=to_dt(u.get("updated_at"), default_now=False),
        ))
        await session.flush()
        user_map[sid(u["_id"])] = new_id
        rep.written["users"] += 1

    # 5 ── user-owned data -----------------------------------------------------
    # symptom checks (user optional)
    rows = []
    for c in mongo_db["symptom_checks"].find():
        rep.read["symptom_checks"] += 1
        rows.append({
            "id": uuid.uuid4(), "user_id": user_map.get(sid(c.get("user_id"))),
            "symptoms": as_list(c.get("symptoms")), "follow_up": c.get("follow_up"),
            "results": c.get("results"), "ai_powered": bool(c.get("ai_powered", False)),
            "created_at": to_dt(c.get("created_at")),
        })
    for batch in chunks(rows):
        await session.execute(pg_insert(SymptomCheck).values(batch))
    rep.written["symptom_checks"] = len(rows)

    # health metrics
    rows = []
    for m in mongo_db["health_metrics"].find():
        rep.read["health_metrics"] += 1
        uid = user_map.get(sid(m.get("user_id")))
        if uid is None:
            rep.skip("health_metrics", "owner user not migrated")
            continue
        if m.get("metric_type") not in METRIC_TYPE_VALUES or m.get("value") is None:
            rep.skip("health_metrics", f"unsupported metric_type {m.get('metric_type')!r}")
            continue
        rows.append({"user_id": uid, "metric_type": m["metric_type"], "value": float(m["value"]),
                     "unit": m.get("unit"), "notes": m.get("notes"), "recorded_at": to_dt(m.get("recorded_at"))})
    for batch in chunks(rows):
        await session.execute(pg_insert(HealthMetric).values(batch))
    rep.written["health_metrics"] = len(rows)

    # health records
    rows = []
    for r in mongo_db["health_records"].find():
        rep.read["health_records"] += 1
        uid = user_map.get(sid(r.get("user_id")))
        if uid is None:
            rep.skip("health_records", "owner user not migrated")
            continue
        rtype = r.get("record_type") if r.get("record_type") in RECORD_TYPE_VALUES else "document"
        rows.append({
            "id": uuid.uuid4(), "user_id": uid, "name": r.get("name") or "Untitled", "record_type": rtype,
            "file_path": r.get("file_path"), "file_size": r.get("file_size"), "mime_type": r.get("mime_type"),
            "tags": as_list(r.get("tags")), "ai_analysis": r.get("ai_analysis"),
            "is_analyzed": bool(r.get("is_analyzed", False)), "uploaded_at": to_dt(r.get("uploaded_at")),
        })
    for batch in chunks(rows):
        await session.execute(pg_insert(HealthRecord).values(batch))
    rep.written["health_records"] = len(rows)

    # chat sessions + messages
    session_map: Dict[str, uuid.UUID] = {}
    rows = []
    for s in mongo_db["chat_sessions"].find():
        rep.read["chat_sessions"] += 1
        uid = user_map.get(sid(s.get("user_id")))
        if uid is None:
            rep.skip("chat_sessions", "owner user not migrated")
            continue
        new_id = uuid.uuid4()
        session_map[sid(s["_id"])] = new_id
        created = to_dt(s.get("created_at"))
        rows.append({"id": new_id, "user_id": uid, "title": (s.get("title") or "")[:200] or None,
                     "language": s.get("language") or "en", "created_at": created,
                     "updated_at": to_dt(s.get("updated_at")) if s.get("updated_at") else created})
    for batch in chunks(rows):
        await session.execute(pg_insert(ChatSession).values(batch))
    rep.written["chat_sessions"] = len(rows)

    msgs = []
    for m in mongo_db["chat_messages"].find().sort("created_at", 1):
        rep.read["chat_messages"] += 1
        sess = session_map.get(sid(m.get("session_id")))
        if sess is None:
            rep.skip("chat_messages", "parent session not migrated")
            continue
        role = m.get("role") if m.get("role") in ("user", "assistant", "system") else "user"
        msgs.append({"session_id": sess, "role": role, "content": m.get("content") or "",
                     "created_at": to_dt(m.get("created_at"))})
    for batch in chunks(msgs):
        await session.execute(pg_insert(ChatMessage).values(batch))
    rep.written["chat_messages"] = len(msgs)

    # hospitals
    rows = []
    for h in mongo_db["hospitals"].find():
        rep.read["hospitals"] += 1
        if not h.get("name"):
            rep.skip("hospitals", "missing name")
            continue
        lat, lng = h.get("latitude"), h.get("longitude")
        if (lat is not None and not -90 <= lat <= 90) or (lng is not None and not -180 <= lng <= 180):
            rep.skip("hospitals", "coordinates out of range")
            continue
        rating = h.get("rating")
        rows.append({
            "name": h["name"], "type": h.get("type"), "address": h.get("address"), "city": h.get("city"),
            "state": h.get("state"), "pincode": h.get("pincode"), "phone": h.get("phone"),
            "email": h.get("email"), "website": h.get("website"), "latitude": lat, "longitude": lng,
            "specialties": as_list(h.get("specialties")),
            "rating": rating if rating is None or 0 <= rating <= 5 else None,
            "is_active": bool(h.get("is_active", True)), "created_at": to_dt(h.get("created_at")),
        })
    for batch in chunks(rows):
        await session.execute(pg_insert(Hospital).values(batch).on_conflict_do_nothing(constraint="uq_hospitals_name_city"))
    rep.written["hospitals"] = len(rows)

    # insurance policies
    rows, seen = [], set()
    for p in mongo_db["insurance_policies"].find():
        rep.read["insurance_policies"] += 1
        uid = user_map.get(sid(p.get("user_id")))
        if uid is None:
            rep.skip("insurance_policies", "owner user not migrated")
            continue
        key = (uid, p.get("policy_number"))
        if not p.get("provider") or not p.get("policy_number") or key in seen:
            rep.skip("insurance_policies", "missing provider/number or duplicate policy number")
            continue
        seen.add(key)
        rows.append({
            "id": uuid.uuid4(), "user_id": uid, "provider": p["provider"], "policy_number": p["policy_number"],
            "policy_type": p.get("policy_type"), "coverage": p.get("coverage"), "premium": p.get("premium"),
            "renewal_date": to_date(p.get("renewal_date")), "status": p.get("status") or "active",
            "notes": p.get("notes"), "created_at": to_dt(p.get("created_at")),
        })
    for batch in chunks(rows):
        await session.execute(pg_insert(InsurancePolicy).values(batch)
                              .on_conflict_do_nothing(constraint="uq_policy_user_number"))
    rep.written["insurance_policies"] = len(rows)

    return rep


# ── CLI ──────────────────────────────────────────────────────────────────────
async def _run(args) -> None:
    from pymongo import MongoClient
    from app.config.database import SessionLocal, close_database

    client = MongoClient(args.mongo_uri, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    mongo_db = client[args.mongo_db]
    print(f"Reading MongoDB '{args.mongo_db}' …")

    async with SessionLocal() as session:
        try:
            report = await migrate(mongo_db, session, keep_empty_organs=args.keep_empty_organs)
            report.print()
            if args.dry_run:
                await session.rollback()
                print("\nDRY RUN — nothing was written. Re-run without --dry-run to apply.")
            else:
                await session.commit()
                print("\nMigration committed.")
        except Exception:
            await session.rollback()
            print("\nMigration FAILED — everything was rolled back.")
            raise
    await close_database()


def main() -> None:
    ap = argparse.ArgumentParser(description="Copy HomeCare+ data from MongoDB into PostgreSQL")
    ap.add_argument("--mongo-uri", default=os.getenv("MONGO_URI", "mongodb://localhost:27017"))
    ap.add_argument("--mongo-db", default=os.getenv("MONGO_DB_NAME", "homecare_plus"))
    ap.add_argument("--dry-run", action="store_true", help="run everything, then roll back")
    ap.add_argument("--keep-empty-organs", action="store_true")
    asyncio.run(_run(ap.parse_args()))


if __name__ == "__main__":
    main()
