"""MongoDB -> PostgreSQL migration, exercised with an in-memory fake MongoDB (mongomock)."""
import datetime as dt

import mongomock
from bson import ObjectId
from sqlalchemy import text

from tests.conftest import db_run
from scripts.migrate_mongo_to_postgres import migrate


def _fake_mongo():
    db = mongomock.MongoClient()["homecare_plus"]
    organ, empty = ObjectId(), ObjectId()
    db.organ_systems.insert_many([
        {"_id": organ, "name": "Legacy Organ", "slug": "legacy-organ", "icon": "x", "specialist": "Doc"},
        {"_id": empty, "name": "Empty Leftover", "slug": "empty-leftover"},
    ])
    db.symptoms.insert_one({"name": "Legacy Itch", "slug": "legacy-itch", "is_common": True})
    db.diseases.insert_many([
        {"name": "Legacy Disease", "slug": "legacy-disease", "icd_code": "Z99", "organ_system_id": str(organ),
         "severity": "severe", "overview": "o", "symptoms": ["legacy itch", "legacy swelling"],
         "causes": ["c1"], "precautions": []},
        {"name": "Legacy Disease", "slug": "legacy-disease", "organ_system_id": str(organ)},   # dup slug
    ])
    u1, u2, u3 = ObjectId(), ObjectId(), ObjectId()
    db.users.insert_many([
        {"_id": u1, "first_name": "Mo", "last_name": "Ngo", "email": "Mo@Legacy.test", "password_hash": "$argon2id$x",
         "date_of_birth": "1991-02-03", "gender": "male", "created_at": dt.datetime(2024, 1, 2, 3, 4, 5)},
        {"_id": u2, "first_name": "Dup", "last_name": "X", "email": "mo@legacy.test", "password_hash": "h"},
        {"_id": u3, "first_name": "No", "last_name": "Pw", "email": "nopw@legacy.test"},
    ])
    db.health_metrics.insert_many([
        {"user_id": str(u1), "metric_type": "heart_rate", "value": 70, "recorded_at": dt.datetime(2024, 5, 1)},
        {"user_id": str(u1), "metric_type": "mystery", "value": 1},
        {"user_id": "ghost", "metric_type": "weight", "value": 1},
    ])
    db.health_records.insert_one({"user_id": str(u1), "name": "r", "record_type": "weird", "tags": ["t"],
                                  "ai_analysis": {"k": 1}})
    s = ObjectId()
    db.chat_sessions.insert_one({"_id": s, "user_id": str(u1), "title": "hi", "language": "hi"})
    db.chat_messages.insert_many([
        {"session_id": str(s), "role": "assistant", "content": "b", "created_at": dt.datetime(2024, 1, 1, 0, 0, 2)},
        {"session_id": str(s), "role": "user", "content": "a", "created_at": dt.datetime(2024, 1, 1, 0, 0, 1)},
    ])
    db.hospitals.insert_many([
        {"name": "Legacy Hospital", "city": "X", "latitude": 10, "longitude": 20, "specialties": ["a"], "rating": 4},
        {"name": "Bad Coords", "city": "X", "latitude": 999, "longitude": 0},
    ])
    db.insurance_policies.insert_one({"user_id": str(u1), "provider": "P", "policy_number": "N1",
                                      "renewal_date": "2026-12-31"})
    db.symptom_checks.insert_one({"user_id": None, "symptoms": ["fever"], "results": [{"a": 1}]})
    return db


def test_migration_roundtrip_and_rerun(client):
    mongo = _fake_mongo()

    def run(commit=True):
        async def go(s):
            rep = await migrate(mongo, s)
            await (s.commit() if commit else s.rollback())
            return rep
        return db_run(go)

    def q(sql):
        async def go(s):
            return (await s.execute(text(sql))).all()
        return db_run(go)

    run(commit=False)                                            # dry run leaves nothing behind
    assert q("select 1 from users where email='mo@legacy.test'") == []

    rep = run()
    assert rep.written["users"] == 1 and len(rep.skipped["users"]) == 2
    assert len(rep.skipped["organ_systems"]) == 1                # empty leftover organ not copied
    assert len(rep.skipped["diseases"]) == 1                     # duplicate slug
    assert len(rep.skipped["health_metrics"]) == 2 and rep.written["health_metrics"] == 1
    assert len(rep.skipped["hospitals"]) == 1

    row = q(("select email, gender, date_of_birth::text, created_at::text, password_hash from users "
                        "where email='mo@legacy.test'"))[0]
    assert row[1] == "male" and row[2] == "1991-02-03" and row[3].startswith("2024-01-02 03:04:05") \
        and row[4] == "$argon2id$x"
    d = q(("select d.severity, d.severity_score, o.name, d.causes, "
                      "(select count(*) from disease_symptoms where disease_id=d.id) "
                      "from diseases d join organ_systems o on o.id=d.organ_system_id where d.slug='legacy-disease'"))[0]
    assert d == ("Severe", 75, "Legacy Organ", ["c1"], 2)
    msgs = q(("select content from chat_messages m join chat_sessions s on s.id=m.session_id "
                         "where s.title='hi' order by m.id"))
    assert [m[0] for m in msgs] == ["a", "b"]                    # chronological order preserved
    assert q(("select record_type, ai_analysis->>'k' from health_records where name='r'")) == [("document", "1")]

    again = run()                                   # re-running is harmless
    assert again.written["users"] == 0
    assert q(("select count(*) from users where lower(email)='mo@legacy.test'"))[0][0] == 1
