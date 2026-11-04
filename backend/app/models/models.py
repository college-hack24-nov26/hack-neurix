"""
HomeCare+ — PostgreSQL schema (SQLAlchemy 2.0 declarative models).

Design notes
------------
* Public catalogue tables (organ_systems, symptoms, diseases, hospitals,
  doctors) use small integer identity keys.
* User-owned tables whose ids appear in URLs/tokens (users, chat_sessions,
  health_records, insurance_policies, symptom_checks, consultations) use UUIDs
  so ids are not guessable/enumerable.
* High-volume append-only tables (health_metrics, chat_messages) use BIGINT.
* Every relationship that Mongo only expressed as a string id is now a real
  foreign key with an explicit ON DELETE rule.
* Disease symptoms are normalised into `disease_symptoms` (many-to-many) with
  an IDF weight, so the symptom checker can be driven by SQL.
* Simple string lists (causes, treatments, tags, specialties…) are native
  Postgres TEXT[]; free-form AI output is JSONB.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Boolean, CheckConstraint, Computed, Date, DateTime, Float,
    ForeignKey, Index, Integer, SmallInteger, String, Text, UniqueConstraint,
    func, text,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ── Allowed value sets (also used for request validation) ────────────────────
GENDER_VALUES = ("male", "female", "other", "prefer_not")
SEVERITY_VALUES = ("Mild", "Moderate", "Severe", "Critical")
RECORD_TYPE_VALUES = ("lab_report", "prescription", "scan", "document", "xray")
METRIC_TYPE_VALUES = (
    "heart_rate", "systolic_bp", "diastolic_bp", "oxygen_level",
    "blood_sugar", "bmi", "weight", "steps", "temperature",
)
HOSPITAL_TYPE_VALUES = ("hospital", "clinic", "pharmacy", "dental")
DOCTOR_STATUS_VALUES = ("available", "busy", "offline")

# Numeric severity used by the symptom checker (0-100), by label.
SEVERITY_SCORE = {"Mild": 25, "Moderate": 55, "Severe": 75, "Critical": 90}


def _in_list(column: str, values: tuple) -> str:
    return f"{column} IN (" + ", ".join(f"'{v}'" for v in values) + ")"


class Base(DeclarativeBase):
    pass


# ── Users ────────────────────────────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(30))
    password_hash: Mapped[str] = mapped_column(String(255))
    date_of_birth: Mapped[Optional[date]] = mapped_column(Date)
    gender: Mapped[Optional[str]] = mapped_column(String(20))
    profile_photo: Mapped[Optional[str]] = mapped_column(String(500))
    language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")
    notification_preferences: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=False, default=dict, server_default=text("'{}'::jsonb"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=utcnow)

    __table_args__ = (
        # Case-insensitive uniqueness: Alice@x.com and alice@x.com are the same account.
        Index("uq_users_email_lower", func.lower(email), unique=True),
        CheckConstraint(_in_list("gender", GENDER_VALUES), name="ck_users_gender"),
    )


class UserActivity(Base):
    __tablename__ = "user_activities"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE")
    )
    action: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(255))
    details: Mapped[Optional[dict]] = mapped_column(JSONB)
    route: Mapped[Optional[str]] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_user_activities_user_created", "user_id", text("created_at DESC")),
    )


# ── Disease library ──────────────────────────────────────────────────────────
class OrganSystem(Base):
    __tablename__ = "organ_systems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True)
    icon: Mapped[Optional[str]] = mapped_column(String(16))
    description: Mapped[Optional[str]] = mapped_column(Text)
    specialist: Mapped[Optional[str]] = mapped_column(String(120))

    diseases: Mapped[List["Disease"]] = relationship(back_populates="organ_system")


class Symptom(Base):
    __tablename__ = "symptoms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(160))
    slug: Mapped[str] = mapped_column(String(160), unique=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    body_part: Mapped[Optional[str]] = mapped_column(String(80))
    is_common: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (
        Index("ix_symptoms_is_common", "is_common"),
        # fast ILIKE '%…%' and similarity() lookups for free-text symptom input
        Index("ix_symptoms_name_trgm", "name", postgresql_using="gin",
              postgresql_ops={"name": "gin_trgm_ops"}),
    )


class Disease(Base):
    __tablename__ = "diseases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    slug: Mapped[str] = mapped_column(String(220), unique=True)
    icd_code: Mapped[Optional[str]] = mapped_column(String(20))
    organ_system_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("organ_systems.id", ondelete="SET NULL")
    )
    category: Mapped[Optional[str]] = mapped_column(String(120))
    severity: Mapped[Optional[str]] = mapped_column(String(20))
    severity_score: Mapped[Optional[int]] = mapped_column(SmallInteger)   # 0-100
    overview: Mapped[Optional[str]] = mapped_column(Text)
    causes: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    risk_factors: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    complications: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    treatments: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    medications: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    home_remedies: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    prevention: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    precautions: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    specialist: Mapped[Optional[str]] = mapped_column(String(120))
    specialist_type: Mapped[Optional[str]] = mapped_column(String(120))
    is_dental: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=utcnow)

    # Weighted full-text document maintained by Postgres itself (never stale).
    search_vector: Mapped[Optional[str]] = mapped_column(
        TSVECTOR,
        Computed(
            "setweight(to_tsvector('english', coalesce(name, '')), 'A') || "
            "setweight(to_tsvector('simple',  coalesce(icd_code, '')), 'A') || "
            "setweight(to_tsvector('english', coalesce(overview, '')), 'B')",
            persisted=True,
        ),
    )

    organ_system: Mapped[Optional[OrganSystem]] = relationship(back_populates="diseases")
    symptom_links: Mapped[List["DiseaseSymptom"]] = relationship(
        back_populates="disease", cascade="all, delete-orphan", passive_deletes=True,
        order_by="DiseaseSymptom.position",
    )

    __table_args__ = (
        CheckConstraint(_in_list("severity", SEVERITY_VALUES), name="ck_diseases_severity"),
        Index("ix_diseases_organ_system_id", "organ_system_id"),
        Index("ix_diseases_category", "category"),
        Index("ix_diseases_icd_code", "icd_code"),
        Index("ix_diseases_search_vector", "search_vector", postgresql_using="gin"),
        Index("ix_diseases_name_trgm", "name", postgresql_using="gin",
              postgresql_ops={"name": "gin_trgm_ops"}),
    )


class DiseaseSymptom(Base):
    """Many-to-many link disease <-> symptom, with an IDF weight and display order."""
    __tablename__ = "disease_symptoms"

    disease_id: Mapped[int] = mapped_column(
        ForeignKey("diseases.id", ondelete="CASCADE"), primary_key=True
    )
    symptom_id: Mapped[int] = mapped_column(
        ForeignKey("symptoms.id", ondelete="CASCADE"), primary_key=True
    )
    # Rare symptoms are more diagnostic than "fever": weight = ln(N / df), see seeding.
    weight: Mapped[float] = mapped_column(Float, default=1.0, server_default=text("1.0"))
    position: Mapped[int] = mapped_column(SmallInteger, default=0, server_default=text("0"))

    disease: Mapped[Disease] = relationship(back_populates="symptom_links")
    symptom: Mapped[Symptom] = relationship()

    __table_args__ = (Index("ix_disease_symptoms_symptom_id", "symptom_id"),)


# ── Symptom-check history ────────────────────────────────────────────────────
class SymptomCheck(Base):
    __tablename__ = "symptom_checks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL")     # keep anonymised stats if the user leaves
    )
    symptoms: Mapped[List[str]] = mapped_column(ARRAY(Text))
    follow_up: Mapped[Optional[dict]] = mapped_column(JSONB)
    results: Mapped[Optional[list]] = mapped_column(JSONB)
    ai_powered: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (Index("ix_symptom_checks_user_created", "user_id", "created_at"),)


# ── Vitals ───────────────────────────────────────────────────────────────────
class HealthMetric(Base):
    __tablename__ = "health_metrics"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    metric_type: Mapped[str] = mapped_column(String(30))
    value: Mapped[float] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(20))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(_in_list("metric_type", METRIC_TYPE_VALUES), name="ck_health_metrics_type"),
        # serves both "latest per type" (DISTINCT ON) and "history in range" queries
        Index("ix_health_metrics_user_type_time", "user_id", "metric_type", text("recorded_at DESC")),
    )


# ── Health records (uploaded files) ──────────────────────────────────────────
class HealthRecord(Base):
    __tablename__ = "health_records"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255))
    record_type: Mapped[str] = mapped_column(String(30), default="document", server_default="document")
    file_path: Mapped[Optional[str]] = mapped_column(String(500))
    file_size: Mapped[Optional[int]] = mapped_column(BigInteger)
    mime_type: Mapped[Optional[str]] = mapped_column(String(100))
    tags: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    is_analyzed: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (
        CheckConstraint(_in_list("record_type", RECORD_TYPE_VALUES), name="ck_health_records_type"),
        Index("ix_health_records_user_uploaded", "user_id", text("uploaded_at DESC")),
        Index("ix_health_records_tags", "tags", postgresql_using="gin"),
    )


# ── Chat ─────────────────────────────────────────────────────────────────────
class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[Optional[str]] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(10), default="en", server_default="en")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now()
    )

    messages: Mapped[List["ChatMessage"]] = relationship(
        back_populates="session", cascade="all, delete-orphan", passive_deletes=True,
        order_by="ChatMessage.id",
    )

    __table_args__ = (Index("ix_chat_sessions_user_updated", "user_id", text("updated_at DESC")),)


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("chat_sessions.id", ondelete="CASCADE"))
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    session: Mapped[ChatSession] = relationship(back_populates="messages")

    __table_args__ = (
        CheckConstraint("role IN ('user', 'assistant', 'system')", name="ck_chat_messages_role"),
        Index("ix_chat_messages_session_id", "session_id", "id"),
    )


# ── Hospitals ────────────────────────────────────────────────────────────────
class Hospital(Base):
    __tablename__ = "hospitals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    type: Mapped[Optional[str]] = mapped_column(String(20))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    pincode: Mapped[Optional[str]] = mapped_column(String(12))
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    website: Mapped[Optional[str]] = mapped_column(String(500))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    specialties: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    rating: Mapped[Optional[float]] = mapped_column(Float)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    __table_args__ = (
        UniqueConstraint("name", "city", name="uq_hospitals_name_city"),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_hospitals_rating"),
        CheckConstraint("latitude IS NULL OR (latitude BETWEEN -90 AND 90)", name="ck_hospitals_lat"),
        CheckConstraint("longitude IS NULL OR (longitude BETWEEN -180 AND 180)", name="ck_hospitals_lng"),
        Index("ix_hospitals_city", "city"),
        Index("ix_hospitals_type", "type"),
        Index("ix_hospitals_lat_lng", "latitude", "longitude"),
        Index("ix_hospitals_name_trgm", "name", postgresql_using="gin",
              postgresql_ops={"name": "gin_trgm_ops"}),
        Index("ix_hospitals_specialties", "specialties", postgresql_using="gin"),
    )


# ── Insurance ────────────────────────────────────────────────────────────────
class InsurancePolicy(Base):
    __tablename__ = "insurance_policies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(200))
    policy_number: Mapped[str] = mapped_column(String(100))
    policy_type: Mapped[Optional[str]] = mapped_column(String(50))
    coverage: Mapped[Optional[str]] = mapped_column(String(100))
    premium: Mapped[Optional[str]] = mapped_column(String(100))
    renewal_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), onupdate=utcnow)

    __table_args__ = (
        UniqueConstraint("user_id", "policy_number", name="uq_policy_user_number"),
        Index("ix_insurance_user_created", "user_id", text("created_at DESC")),
    )


# ── Telemedicine (previously an in-memory list) ──────────────────────────────
class Doctor(Base):
    __tablename__ = "doctors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(150), unique=True)
    specialization: Mapped[str] = mapped_column(String(100))
    hospital: Mapped[Optional[str]] = mapped_column(String(200))
    experience: Mapped[Optional[int]] = mapped_column(SmallInteger)          # years
    rating: Mapped[Optional[float]] = mapped_column(Float)
    fee: Mapped[int] = mapped_column(Integer, default=0, server_default=text("0"))
    languages: Mapped[List[str]] = mapped_column(ARRAY(Text), default=list, server_default=text("'{}'"))
    status: Mapped[str] = mapped_column(String(20), default="available", server_default="available")

    __table_args__ = (
        CheckConstraint(_in_list("status", DOCTOR_STATUS_VALUES), name="ck_doctors_status"),
        CheckConstraint("fee >= 0", name="ck_doctors_fee"),
        Index("ix_doctors_specialization", "specialization"),
    )


class Consultation(Base):
    __tablename__ = "consultations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    booking_ref: Mapped[str] = mapped_column(String(40), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    doctor_id: Mapped[int] = mapped_column(ForeignKey("doctors.id", ondelete="RESTRICT"))
    slot: Mapped[str] = mapped_column(String(60))
    consult_type: Mapped[str] = mapped_column(String(20), default="video", server_default="video")
    reason: Mapped[Optional[str]] = mapped_column(Text)
    fee: Mapped[int] = mapped_column(Integer)                                # fee charged at booking time
    status: Mapped[str] = mapped_column(String(20), default="confirmed", server_default="confirmed")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    doctor: Mapped[Doctor] = relationship()

    __table_args__ = (
        CheckConstraint("consult_type IN ('video', 'chat', 'audio')", name="ck_consult_type"),
        CheckConstraint("status IN ('confirmed', 'completed', 'cancelled')", name="ck_consult_status"),
        Index("ix_consultations_user_created", "user_id", text("created_at DESC")),
    )


class ConsultationPrescription(Base):
    __tablename__ = "consultation_prescriptions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    consultation_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("consultations.id", ondelete="CASCADE"), unique=True
    )
    uploaded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(Integer)
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, server_default=func.now()
    )

    consultation: Mapped[Consultation] = relationship()
    uploader: Mapped[User] = relationship()

    __table_args__ = (
        Index("ix_consultation_prescriptions_consultation", "consultation_id"),
    )


# ── Home laboratory testing ──────────────────────────────────────────────────
class Laboratory(Base):
    __tablename__ = "laboratories"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[Optional[str]] = mapped_column(Text)
    city: Mapped[Optional[str]] = mapped_column(String(100))
    state: Mapped[Optional[str]] = mapped_column(String(100))
    pincode: Mapped[Optional[str]] = mapped_column(String(12))
    phone: Mapped[Optional[str]] = mapped_column(String(40))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)
    rating: Mapped[Optional[float]] = mapped_column(Float)
    home_collection: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    verification_status: Mapped[str] = mapped_column(String(20), default="pending", server_default="pending")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("name", "city", name="uq_laboratories_name_city"),
        CheckConstraint("verification_status IN ('pending', 'verified', 'rejected')", name="ck_laboratories_verification"),
        CheckConstraint("rating IS NULL OR (rating >= 0 AND rating <= 5)", name="ck_laboratories_rating"),
        Index("ix_laboratories_city", "city"),
        Index("ix_laboratories_home_collection", "home_collection"),
        Index("ix_laboratories_lat_lng", "latitude", "longitude"),
    )


class LaboratoryTest(Base):
    __tablename__ = "laboratory_tests"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    laboratory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    category: Mapped[str] = mapped_column(String(50))
    description: Mapped[Optional[str]] = mapped_column(Text)
    sample_type: Mapped[Optional[str]] = mapped_column(String(100))
    preparation: Mapped[Optional[str]] = mapped_column(Text)
    turnaround_hours: Mapped[Optional[int]] = mapped_column(Integer)
    price: Mapped[float] = mapped_column(Float, default=0, server_default=text("0"))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

    __table_args__ = (
        UniqueConstraint("laboratory_id", "name", name="uq_lab_test_lab_name"),
        CheckConstraint("price >= 0", name="ck_lab_test_price"),
        Index("ix_lab_tests_name", "name"),
        Index("ix_lab_tests_category", "category"),
    )


class LaboratoryServiceArea(Base):
    __tablename__ = "laboratory_service_areas"

    laboratory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratories.id", ondelete="CASCADE"), primary_key=True)
    pincode: Mapped[str] = mapped_column(String(12), primary_key=True)
    home_collection_fee: Mapped[float] = mapped_column(Float, default=0, server_default=text("0"))


class LabBooking(Base):
    __tablename__ = "lab_bookings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    booking_ref: Mapped[str] = mapped_column(String(40), unique=True)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    laboratory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratories.id", ondelete="RESTRICT"))
    patient_name: Mapped[str] = mapped_column(String(200))
    patient_phone: Mapped[str] = mapped_column(String(30))
    address: Mapped[str] = mapped_column(Text)
    pincode: Mapped[str] = mapped_column(String(12))
    landmark: Mapped[Optional[str]] = mapped_column(Text)
    preferred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    special_instructions: Mapped[Optional[str]] = mapped_column(Text)
    test_total: Mapped[float] = mapped_column(Float)
    collection_fee: Mapped[float] = mapped_column(Float, default=0, server_default=text("0"))
    status: Mapped[str] = mapped_column(String(30), default="booking_requested", server_default="booking_requested")
    status_history: Mapped[list] = mapped_column(JSONB, default=list, server_default=text("'[]'::jsonb"))
    professional_name: Mapped[Optional[str]] = mapped_column(String(200))
    professional_phone: Mapped[Optional[str]] = mapped_column(String(30))
    professional_verified: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, server_default=func.now())

    __table_args__ = (
        CheckConstraint("status IN ('booking_requested', 'booking_confirmed', 'phlebotomist_assigned', 'professional_on_the_way', 'sample_collected', 'sample_received', 'test_in_progress', 'report_ready', 'report_uploaded', 'completed', 'cancelled', 'rejected')", name="ck_lab_booking_status"),
        CheckConstraint("test_total >= 0 AND collection_fee >= 0", name="ck_lab_booking_amounts"),
        Index("ix_lab_bookings_user_created", "user_id", text("created_at DESC")),
        Index("ix_lab_bookings_lab_status", "laboratory_id", "status"),
    )


class LabBookingTest(Base):
    __tablename__ = "lab_booking_tests"

    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lab_bookings.id", ondelete="CASCADE"), primary_key=True)
    test_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratory_tests.id", ondelete="RESTRICT"), primary_key=True)
    price: Mapped[float] = mapped_column(Float)


class LabReport(Base):
    __tablename__ = "lab_reports"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("lab_bookings.id", ondelete="CASCADE"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    laboratory_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("laboratories.id", ondelete="RESTRICT"))
    title: Mapped[str] = mapped_column(String(255))
    file_path: Mapped[str] = mapped_column(String(500))
    mime_type: Mapped[str] = mapped_column(String(100))
    file_size: Mapped[int] = mapped_column(BigInteger)
    ai_analysis: Mapped[Optional[dict]] = mapped_column(JSONB)
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())

    __table_args__ = (Index("ix_lab_reports_user_uploaded", "user_id", text("uploaded_at DESC")),)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=text("gen_random_uuid()"))
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    title: Mapped[str] = mapped_column(String(200))
    message: Mapped[str] = mapped_column(Text)
    type: Mapped[str] = mapped_column(String(50), default="info", server_default="info")
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("false"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, server_default=func.now())
