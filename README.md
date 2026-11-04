# HomeCare+ — AI Healthcare Platform

A full-stack AI-powered digital healthcare platform: symptom analysis, health monitoring, medical
records, AI chat, hospital finder, insurance tracker, telemedicine and AI-assisted image/report
analysis. Backend: **FastAPI + PostgreSQL** (SQLAlchemy 2.0 async, Alembic). Frontend: React + Vite.

AI uses a multi-model fallback chain (Groq → Anthropic → OpenAI → offline rules), so the whole app
also works with **no API keys at all**.

> Migrating an existing MongoDB install? See **[POSTGRES_MIGRATION.md](POSTGRES_MIGRATION.md)**.

---

## What's in this release (MongoDB → PostgreSQL)

* **14-table relational schema** with real foreign keys, CHECK constraints, indexes, `TEXT[]` and `JSONB` columns,
  managed by **Alembic** migrations.
* **Symptom checker is database-driven.** All ~347 diseases are scored in SQL using a normalised
  `disease_symptoms` table with **IDF weights** (a rare symptom like *Koplik spots* counts far more than *fever*).
  Previously only a hard-coded list of 57 diseases was used when no AI key was configured.
* **Disease library data filled in.** Precautions, home remedies, medications, severity scores and specialists from the
  symptom-checker knowledge base are merged into the matching disease records (57 diseases).
  13 diseases that the dataset listed under two organ systems are merged into one record.
* **Better search.** Weighted full-text search + typo-tolerant trigram matching over name, ICD code and overview,
  plus search by symptom (`/api/diseases/search?q=koplik`). Disease detail works by id *or* slug.
* **Searchable symptom catalogue** of ~960 symptoms (`/api/symptoms/list`) now powers the Symptom Checker's search box.
* **Hospitals "nearby"** computed and sorted in SQL (bounding-box + haversine); search also matches specialties.
* **Telemedicine** doctors and bookings are stored in the database (they were an in-memory list).
* Fewer queries: chat history, vitals dashboard and organ counts each take 1–2 queries instead of N+1.
* LLM calls no longer block the server's event loop, and no database connection is held while waiting for them.
* Existing bug fixed: the two old seeders created duplicate/empty organ systems.

---

## Quick start

### Option A — Docker (everything)

```bash
cp backend/.env.example backend/.env       # optional: add AI keys, set SECRET_KEY
docker compose up --build
```

Starts PostgreSQL, applies the migrations, loads the disease library / hospitals / doctors, then serves
the frontend at http://localhost:3000 and the API at http://localhost:8100 (docs: `/api/docs`).
PostgreSQL is exposed on host port **5433**.

### Option B — Manual

Prerequisites: Python 3.11+, Node 18+, PostgreSQL 13+ (`pg_trgm` extension — included in standard installs).

```bash
# 1. database
createdb homecare_plus                       # or: docker compose up -d postgres  (port 5433)

# 2. backend
cd backend
python -m venv venv && source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                  # set DATABASE_URL (+ optional AI keys)
alembic upgrade head                                  # create the schema
python seed_db.py                                     # load diseases, symptoms, hospitals, doctors, demo user
uvicorn main:app --reload --port 8000

# 3. frontend
cd ../frontend && npm install && npm run dev          # http://localhost:3000
```

API docs: http://localhost:8000/api/docs · health: http://localhost:8000/api/health-check

Demo login (non-production only): `demo@homecare.plus` / `Demo@1234`

---

## Environment variables (`backend/.env`)

| Variable | Purpose | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL URL (`postgres://`, `postgresql://` and `postgresql+asyncpg://` all accepted) | `postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_plus` |
| `DB_POOL_SIZE` / `DB_MAX_OVERFLOW` | Connection pool | `10` / `20` |
| `SECRET_KEY` | JWT signing key — **required to change when `APP_ENV=production`** | placeholder |
| `GROQ_API_KEY` | Primary chat model | optional |
| `ANTHROPIC_API_KEY` | Vision analysis + chat fallback | optional |
| `OPENAI_API_KEY` | Final fallback for chat + vision | optional |
| `GOOGLE_MAPS_API_KEY` | Hospital map | optional |
| `ALLOWED_ORIGINS` | CORS origins (JSON list) | localhost dev origins |

## Database workflow

```bash
alembic upgrade head                                   # apply migrations
alembic revision --autogenerate -m "describe change"   # after editing app/models/models.py
alembic downgrade -1                                   # roll back one migration
python seed_db.py                                      # idempotent; safe to re-run
```

## Tests

```bash
cd backend
createdb homecare_test
pip install -r requirements-dev.txt
TEST_DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/homecare_test pytest
```

The suite runs against a real PostgreSQL database (it drops and recreates the schema of the *test* database)
and covers every route group, the seeder, symptom scoring and the MongoDB migration script.

## How the multi-model AI fallback works

```
Chat message ─▶ Groq ─▶ Anthropic Claude ─▶ OpenAI GPT ─▶ rule-based offline response
```

Image/report analysis tries only vision-capable providers (Claude → GPT-4o → mock fallback).
Symptom analysis tries the LLM first, then the PostgreSQL disease library. Responses include an
`ai_powered` flag so the UI can show whether a real model answered.

## Project structure

```
backend/
├── alembic/                    # migrations (0001 = initial PostgreSQL schema)
├── app/
│   ├── config/                 # settings.py (env), database.py (async engine/session)
│   ├── data/disease_dataset.py # organ systems + diseases dataset (pure data)
│   ├── middleware/auth.py      # JWT + Argon2
│   ├── models/models.py        # SQLAlchemy models
│   ├── routes/                 # auth, symptoms, diseases, chat, health, records, hospitals,
│   │                           #   insurance, analysis, user, telemedicine
│   ├── services/               # ai_service, symptom_service, symptom_db_service, analysis_service
│   └── seeding.py              # idempotent seeders (dataset merge, IDF weights)
├── scripts/migrate_mongo_to_postgres.py
├── tests/
├── seed_db.py  seed_diseases.py  main.py
frontend/                       # React + Vite
docker-compose.yml              # postgres + backend + frontend
```

## Production checklist

- [ ] Set `APP_ENV=production`, `DEBUG=False` and a random `SECRET_KEY` (`python -c "import secrets; print(secrets.token_urlsafe(48))"`)
- [ ] Use a managed PostgreSQL (or a password-protected one), not the default `homecare/homecare` credentials; add `?ssl=require` if your host needs TLS
- [ ] Run `alembic upgrade head` as a deploy step
- [ ] Configure `ALLOWED_ORIGINS` for your domain
- [ ] Set at least one AI key for full AI functionality
- [ ] Put `backend/uploads` on persistent / object storage
- [ ] Schedule `pg_dump` backups
- [ ] Never commit `backend/.env` — rotate any API key that has ever been committed or shared
