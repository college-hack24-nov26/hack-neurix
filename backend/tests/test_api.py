import io
from pathlib import Path


# ── seed data ────────────────────────────────────────────────────────────────
def test_seed_loaded_and_enriched(client):
    organs = client.get("/api/diseases/organs").json()["organs"]
    assert len(organs) == 18
    assert sum(o["count"] for o in organs) == 347          # 360 dataset rows - 13 duplicates merged
    d = client.get("/api/diseases/hypertension").json()
    assert d["icd_code"] == "I10" and "Monitor BP daily" in d["precautions"]
    assert len(d["symptoms"]) >= 8
    assert len(client.get("/api/symptoms/list").json()["symptoms"]) > 900


def test_seed_is_idempotent(client):
    from app.seeding import seed_all
    from tests.conftest import db_run

    async def run(s):
        async with s.begin():
            return await seed_all(s)
    counts = db_run(run)
    assert counts["diseases"] == 347 and counts["organ_systems"] == 18 and counts["hospitals"] == 6


# ── auth ─────────────────────────────────────────────────────────────────────
def test_register_login_profile_password(client):
    r = client.post("/api/auth/register", json={
        "firstName": "Ana", "lastName": "Lee", "email": "Ana.Lee@Example.com", "password": "Password123",
        "gender": "", "dateOfBirth": "", "phone": ""})
    assert r.status_code == 201
    assert r.json()["user"]["email"] == "ana.lee@example.com" and r.json()["user"]["gender"] is None
    dup = client.post("/api/auth/register", json={
        "firstName": "A", "lastName": "B", "email": "ANA.LEE@example.com", "password": "Password123"})
    assert dup.status_code == 409

    login = client.post("/api/auth/login", json={"email": "ana.lee@EXAMPLE.com", "password": "Password123"})
    assert login.status_code == 200
    h = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.post("/api/auth/login", json={"email": "ana.lee@example.com", "password": "nope"}).status_code == 401

    p = client.put("/api/auth/profile", headers=h, json={"firstName": "Anna", "gender": "female",
                                                          "dateOfBirth": "1990-05-17"})
    assert p.json()["user"]["firstName"] == "Anna" and p.json()["user"]["dateOfBirth"] == "1990-05-17"
    assert client.put("/api/auth/profile", headers=h, json={"gender": "robot"}).status_code == 422

    assert client.put("/api/auth/password", headers=h,
                      json={"currentPassword": "wrong", "newPassword": "NewPassword1"}).status_code == 400
    assert client.put("/api/auth/password", headers=h,
                      json={"currentPassword": "Password123", "newPassword": "NewPassword1"}).status_code == 200
    assert client.post("/api/auth/login", json={"email": "ana.lee@example.com",
                                                "password": "NewPassword1"}).status_code == 200


def test_bad_tokens_rejected(client):
    assert client.get("/api/auth/profile").status_code in (401, 403)
    assert client.get("/api/auth/profile", headers={"Authorization": "Bearer garbage"}).status_code == 401
    from app.middleware.auth import create_access_token
    legacy = create_access_token({"sub": "64b7f0c2a1b2c3d4e5f60718"})      # old Mongo ObjectId
    assert client.get("/api/auth/profile", headers={"Authorization": f"Bearer {legacy}"}).status_code == 401


# ── disease library ──────────────────────────────────────────────────────────
def test_disease_list_filters_and_pagination(client):
    r = client.get("/api/diseases", params={"per_page": 10, "page": 2}).json()
    assert r["total"] == 347 and len(r["diseases"]) == 10
    r = client.get("/api/diseases", params={"organ": "cardiovascular"}).json()
    assert r["total"] == 20 and all(d["organ"] == "Cardiovascular" for d in r["diseases"])
    assert client.get("/api/diseases", params={"organ": "nope"}).json()["total"] == 0
    assert client.get("/api/diseases/organ/nope").status_code == 404


def test_disease_search(client):
    names = lambda q: [d["name"] for d in client.get("/api/diseases/search", params={"q": q}).json()["results"]]
    assert names("hypertension")[0] == "Hypertension"
    assert names("hypertenson")[0] == "Hypertension"           # typo tolerant
    assert names("I10")[0] == "Hypertension"                   # ICD code
    assert "Measles" in names("koplik spots")                  # found via symptom
    assert names("100%_") == []                                # wildcards are literal


def test_disease_detail_by_id_and_slug_and_404(client):
    by_slug = client.get("/api/diseases/asthma").json()
    by_id = client.get(f"/api/diseases/{by_slug['id']}").json()
    assert by_id["name"] == "Asthma"
    assert client.get("/api/diseases/999999").status_code == 404
    assert client.get("/api/diseases/not-a-disease").status_code == 404


# ── symptom checker ──────────────────────────────────────────────────────────
def _analyze(client, symptoms, **kw):
    r = client.post("/api/symptoms/analyze", json={"symptoms": symptoms, **kw})
    assert r.status_code == 200, r.text
    return r.json()


def test_symptom_checker_db_scoring(client):
    out = _analyze(client, ["koplik spots", "fever", "skin rash"])
    assert out["ai_powered"] is False
    assert out["possible_diseases"][0]["name"] == "Measles"     # rare symptom outweighs common ones
    flu = _analyze(client, ["Fever", "cough", "body aches"])["possible_diseases"]
    assert "Influenza" in [d["name"] for d in flu]
    typo = _analyze(client, ["headche"])["possible_diseases"]
    assert typo and all(0 <= d["probability"] <= 100 for d in typo)
    assert _analyze(client, ["zzzz-not-a-symptom"])["possible_diseases"] == []
    for d in flu:                                               # every result is actionable
        assert d["precautions"] and d["description"] and d["specialist"]


def test_symptom_check_is_persisted(client, user):
    _analyze_h = client.post("/api/symptoms/analyze", headers=user["headers"], json={"symptoms": ["fever"]})
    assert _analyze_h.status_code == 200
    from sqlalchemy import text
    from tests.conftest import db_run

    async def count(s):
        return (await s.execute(text("select count(*) from symptom_checks where user_id = cast(:u as uuid)"),
                                {"u": user["id"]})).scalar_one()
    assert db_run(count) == 1
    assert client.post("/api/symptoms/analyze", json={"symptoms": []}).status_code == 422
    assert len(client.get("/api/symptoms/list", params={"common_only": True}).json()["symptoms"]) > 20
    assert client.get("/api/symptoms/list", params={"q": "chest"}).json()["symptoms"]


# ── vitals ───────────────────────────────────────────────────────────────────
def test_vitals_flow(client, user, other_user):
    h = user["headers"]
    assert client.post("/api/health/metrics", headers=h, json={}).status_code == 400
    r = client.post("/api/health/metrics", headers=h, json={"heart_rate": 72, "systolic_bp": 135, "notes": "x"})
    assert r.json()["count"] == 2
    client.post("/api/health/metrics", headers=h, json={"heart_rate": 88})
    latest = client.get("/api/health/metrics", headers=h).json()["metrics"]
    assert latest["heart_rate"]["value"] == 88 and latest["systolic_bp"]["status"] == "high"
    hist = client.get("/api/health/metrics/heart_rate", headers=h, params={"days": 7}).json()
    assert [x["value"] for x in hist["readings"]] == [72, 88]
    assert client.get("/api/health/metrics/bogus", headers=h).status_code == 400
    dash = client.get("/api/health/dashboard", headers=h).json()
    assert len(dash["heart_rate_trend"]) == 2 and dash["health_score"] == 50
    assert client.get("/api/health/metrics", headers=other_user["headers"]).json()["metrics"] == {}


# ── records ──────────────────────────────────────────────────────────────────
def test_records_flow_and_isolation(client, user, other_user):
    h = user["headers"]
    pdf = ("lab.pdf", io.BytesIO(b"%PDF-1.4 test"), "application/pdf")
    r = client.post("/api/records/upload", headers=h, files={"file": pdf},
                    data={"name": "Blood test", "record_type": "lab_report", "tags": "a, b"})
    assert r.status_code == 201
    rec = r.json()
    assert rec["tags"] == ["a", "b"] and Path(rec["file_path"]).exists()
    assert len(client.get("/api/records", headers=h).json()["records"]) == 1
    assert client.get(f"/api/records/{rec['id']}", headers=other_user["headers"]).status_code == 404
    assert client.delete(f"/api/records/{rec['id']}", headers=other_user["headers"]).status_code == 404
    assert client.get("/api/records/not-a-uuid", headers=h).status_code == 404
    bad = client.post("/api/records/upload", headers=h, data={"name": "x"},
                      files={"file": ("a.exe", io.BytesIO(b"x"), "application/x-msdownload")})
    assert bad.status_code == 400
    badtype = client.post("/api/records/upload", headers=h, data={"name": "x", "record_type": "weird"},
                          files={"file": ("a.pdf", io.BytesIO(b"x"), "application/pdf")})
    assert badtype.status_code == 400
    assert client.delete(f"/api/records/{rec['id']}", headers=h).status_code == 204
    assert not Path(rec["file_path"]).exists()


# ── chat ─────────────────────────────────────────────────────────────────────
def test_chat_flow(client, user):
    h = user["headers"]
    r = client.post("/api/chat/message", headers=h,
                    json={"messages": [{"role": "user", "content": "I have a headache"}], "language": "hi"})
    assert r.status_code == 200 and r.json()["ai_powered"] is False
    client.post("/api/chat/message", headers=h,
                json={"messages": [{"role": "user", "content": "and a fever"}], "language": "en"})
    hist = client.get("/api/chat/history", headers=h).json()["sessions"]
    assert len(hist) == 1 and [m["role"] for m in hist[0]["messages"]] == ["user", "assistant"] * 2
    assert client.post("/api/chat/message", headers=h, json={"messages": []}).status_code == 400
    assert client.delete("/api/chat/history", headers=h).status_code == 200
    assert client.get("/api/chat/history", headers=h).json()["sessions"] == []


# ── hospitals ────────────────────────────────────────────────────────────────
def test_hospitals(client):
    near = client.get("/api/hospitals/nearby", params={"lat": 18.5204, "lng": 73.8567, "radius": 10}).json()
    assert len(near["hospitals"]) == 6
    dists = [h["distance_km"] for h in near["hospitals"]]
    assert dists == sorted(dists) and dists[0] < 0.1
    tight = client.get("/api/hospitals/nearby", params={"lat": 18.5204, "lng": 73.8567, "radius": 0.5}).json()
    assert 0 < len(tight["hospitals"]) < 6
    assert client.get("/api/hospitals/nearby", params={"lat": 28.6, "lng": 77.2}).json()["hospitals"] == []
    only = client.get("/api/hospitals/nearby", params={"lat": 18.52, "lng": 73.85, "type": "dental"}).json()
    assert [h["name"] for h in only["hospitals"]] == ["Smile Dental Clinic"]
    # python and SQL haversine agree
    from app.routes.hospitals import haversine
    h0 = near["hospitals"][-1]
    assert abs(haversine(18.5204, 73.8567, h0["latitude"], h0["longitude"]) - h0["distance_km"]) < 0.01
    assert [h["name"] for h in client.get("/api/hospitals/search", params={"q": "cardio"}).json()["results"]]
    assert client.get("/api/hospitals/search", params={"q": "ruby"}).json()["results"][0]["name"] == "Ruby Hall Clinic"
    hid = near["hospitals"][0]["id"]
    assert client.get(f"/api/hospitals/{hid}").status_code == 200
    assert client.get("/api/hospitals/abc").status_code == 404


# ── insurance ────────────────────────────────────────────────────────────────
def test_insurance_crud(client, user, other_user):
    h = user["headers"]
    body = {"provider": "Star Health", "policyNumber": "P-1", "coverage": "500000", "renewalDate": ""}
    r = client.post("/api/insurance", headers=h, json=body)
    assert r.status_code == 201
    pid = r.json()["id"]
    assert client.post("/api/insurance", headers=h, json=body).status_code == 409
    assert client.post("/api/insurance", headers=other_user["headers"], json=body).status_code == 201
    u = client.put(f"/api/insurance/{pid}", headers=h, json={"status": "expired", "renewalDate": "2027-01-31"})
    assert u.json()["status"] == "expired" and u.json()["renewalDate"] == "2027-01-31"
    assert client.put(f"/api/insurance/{pid}", headers=other_user["headers"], json={}).status_code == 404
    assert len(client.get("/api/insurance", headers=h).json()["policies"]) == 1
    assert client.delete(f"/api/insurance/{pid}", headers=h).status_code == 204
    assert client.get("/api/insurance", headers=h).json()["policies"] == []


# ── telemedicine ─────────────────────────────────────────────────────────────
def test_telemedicine(client, user):
    docs = client.get("/api/telemedicine/doctors").json()["doctors"]
    assert len(docs) == 8
    assert len(client.get("/api/telemedicine/doctors", params={"specialization": "cardiologist"}).json()["doctors"]) == 1
    offline = next(d for d in docs if d["status"] == "offline")
    h = user["headers"]
    assert client.post("/api/telemedicine/book", headers=h,
                       json={"doctor_id": offline["id"], "slot": "10:00 AM"}).status_code == 400
    assert client.post("/api/telemedicine/book", headers=h, json={"doctor_id": 9999, "slot": "x"}).status_code == 404
    ok = client.post("/api/telemedicine/book", headers=h, json={"doctor_id": docs[0]["id"], "slot": "09:00 AM"})
    assert ok.status_code == 200 and ok.json()["booking_id"].startswith("BK")
    mine = client.get("/api/telemedicine/consultations", headers=h).json()["consultations"]
    assert len(mine) == 1 and mine[0]["doctor"] == docs[0]["name"]
