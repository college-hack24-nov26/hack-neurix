# MongoDB → PostgreSQL migration guide

## 1. Collection → table mapping

| MongoDB collection | PostgreSQL table | Notes |
|---|---|---|
| `users` | `users` | UUID primary key; case-insensitive unique email (`lower(email)` index); `gender` constrained; password hashes unchanged |
| `organ_systems` | `organ_systems` | integer id; `slug` unique |
| `symptoms` | `symptoms` | slug unique; trigram index for search; `is_common` marks quick-pick chips |
| `diseases` (with `symptoms: [..]`) | `diseases` + `disease_symptoms` | symptoms became a many-to-many table with an IDF `weight`; list fields are `TEXT[]`; generated `tsvector` column + GIN index; `organ_system_id` is a real FK |
| `symptom_checks` | `symptom_checks` | `results` / `follow_up` are `JSONB`; `user_id` FK (`SET NULL`) |
| `health_metrics` | `health_metrics` | BIGINT id; FK `CASCADE`; composite index `(user_id, metric_type, recorded_at DESC)` |
| `health_records` | `health_records` | `tags TEXT[]`, `ai_analysis JSONB`; FK `CASCADE` |
| `chat_sessions` + `chat_messages` | same | messages FK `CASCADE` (deleting a session deletes its messages) |
| `hospitals` | `hospitals` | `specialties TEXT[]`; lat/lng + rating CHECKs; unique `(name, city)` |
| `insurance_policies` | `insurance_policies` | `renewal_date` is a real `DATE`; unique `(user_id, policy_number)` |
| *(in-memory list)* | `doctors`, `consultations` | telemedicine is now persisted |

## 2. API compatibility

Request/response shapes are unchanged, so the React frontend needs no changes to keep working
(the only frontend edit is the optional Symptom Checker search box, which now uses the full symptom catalogue).
Ids are still strings in responses. Differences you may notice:

* Ids are UUIDs (user data) or small integers (catalogue data) instead of ObjectIds.
* `/api/diseases/{id}` also accepts a slug. `/api/symptoms/list` returns ~960 symptoms (`?common_only=true`, `?q=` supported).
* Stricter validation returns `422`/`400` instead of storing junk: unknown `gender`, `record_type`, `metric_type`, `NaN`/`Infinity` vitals.
* Duplicate insurance policy numbers per user return `409`.
* **Existing login tokens stop working** (they carried a Mongo ObjectId). Users just sign in again — their passwords still work.

## 3. Migrating existing data

```bash
cd backend
pip install -r requirements-migration.txt
alembic upgrade head                           # create the schema (empty tables)

# rehearsal — runs everything, then rolls back
python -m scripts.migrate_mongo_to_postgres --mongo-uri mongodb://localhost:27017 --mongo-db homecare_plus --dry-run

# for real (single transaction: all or nothing)
python -m scripts.migrate_mongo_to_postgres --mongo-uri mongodb://localhost:27017 --mongo-db homecare_plus

python seed_db.py                              # optional: fills in anything the library is missing
```

The script prints a per-collection table (read / written / skipped) and the reasons for skipped rows
(for example metrics with an unsupported type, duplicate policy numbers, orphaned child rows). It is safe to re-run.

* Uploaded files are not moved: keep the same `UPLOAD_DIR`, or copy the folder and update `file_path`.
* Organ systems created by the old `seed_db.py` that have no diseases (leftovers of the old double-seeding) are
  skipped; use `--keep-empty-organs` to copy them anyway.
* Starting from scratch instead? Skip all of this: `alembic upgrade head && python seed_db.py`.

## 4. Dataset improvements (what changed in the data)

* 360 dataset rows → **347 unique diseases** (13 listed under two organ systems were merged; symptoms unioned,
  higher severity kept). Previously the second copy was silently dropped.
* **962 symptoms** extracted from the dataset, linked to diseases (2,290 links) with IDF weights.
* **57 diseases** enriched with precautions / home remedies / medications / severity score / specialist from the
  symptom-checker knowledge base (53 matched by name, 4 by ICD code: Acne Vulgaris, Major Depression,
  Generalized Anxiety Disorder, Systemic Lupus Erythematosus).
* Not covered by any source data: `causes`, `risk_factors`, `complications`, `treatments`, `prevention` are empty for all
  diseases, and treatment info is empty for the ~290 diseases outside the knowledge base. The API and UI handle empty
  lists, and the symptom checker falls back to "consult a <specialist>" guidance. Filling these needs reviewed medical
  content — the schema is ready for it.

## 5. Rollback

The old MongoDB database is never modified. To go back, deploy the previous version of the code against it.
