"""Add Home Lab models.

Revision ID: 0002
Revises: 0001
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "laboratories",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("state", sa.String(100), nullable=True),
        sa.Column("pincode", sa.String(12), nullable=True),
        sa.Column("phone", sa.String(40), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("rating", sa.Float(), nullable=True),
        sa.Column("home_collection", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("verification_status", sa.String(20), server_default="pending", nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", "city", name="uq_laboratories_name_city"),
        sa.CheckConstraint("verification_status IN ('pending', 'verified', 'rejected')", name="ck_laboratories_verification"),
    )
    op.create_index("ix_laboratories_city", "laboratories", ["city"])
    op.create_index("ix_laboratories_home_collection", "laboratories", ["home_collection"])
    op.create_index("ix_laboratories_lat_lng", "laboratories", ["latitude", "longitude"])

    op.create_table(
        "laboratory_tests",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("category", sa.String(50), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sample_type", sa.String(100), nullable=True),
        sa.Column("preparation", sa.Text(), nullable=True),
        sa.Column("turnaround_hours", sa.Integer(), nullable=True),
        sa.Column("price", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.ForeignKeyConstraint(["laboratory_id"], ["laboratories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("laboratory_id", "name", name="uq_lab_test_lab_name"),
        sa.CheckConstraint("price >= 0", name="ck_lab_test_price"),
    )
    op.create_index("ix_lab_tests_name", "laboratory_tests", ["name"])
    op.create_index("ix_lab_tests_category", "laboratory_tests", ["category"])

    op.create_table(
        "laboratory_service_areas",
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("pincode", sa.String(12), nullable=False),
        sa.Column("home_collection_fee", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.ForeignKeyConstraint(["laboratory_id"], ["laboratories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("laboratory_id", "pincode"),
    )

    op.create_table(
        "lab_bookings",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("booking_ref", sa.String(40), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("patient_name", sa.String(200), nullable=False),
        sa.Column("patient_phone", sa.String(30), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("pincode", sa.String(12), nullable=False),
        sa.Column("landmark", sa.Text(), nullable=True),
        sa.Column("preferred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("special_instructions", sa.Text(), nullable=True),
        sa.Column("test_total", sa.Float(), nullable=False),
        sa.Column("collection_fee", sa.Float(), server_default=sa.text("0"), nullable=False),
        sa.Column("status", sa.String(30), server_default="booking_requested", nullable=False),
        sa.Column("status_history", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column("professional_name", sa.String(200), nullable=True),
        sa.Column("professional_phone", sa.String(30), nullable=True),
        sa.Column("professional_verified", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("booking_ref"),
        sa.CheckConstraint("status IN ('booking_requested', 'booking_confirmed', 'phlebotomist_assigned', 'professional_on_the_way', 'sample_collected', 'sample_received', 'test_in_progress', 'report_ready', 'report_uploaded', 'completed', 'cancelled', 'rejected')", name="ck_lab_booking_status"),
        sa.CheckConstraint("test_total >= 0 AND collection_fee >= 0", name="ck_lab_booking_amounts"),
    )
    op.create_index("ix_lab_bookings_user_created", "lab_bookings", ["user_id", "created_at"])
    op.create_index("ix_lab_bookings_lab_status", "lab_bookings", ["laboratory_id", "status"])

    op.create_table(
        "lab_booking_tests",
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("test_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("price", sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["lab_bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["test_id"], ["laboratory_tests.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("booking_id", "test_id"),
    )

    op.create_table(
        "lab_reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("booking_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("laboratory_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("ai_analysis", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["booking_id"], ["lab_bookings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["laboratory_id"], ["laboratories.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_lab_reports_user_uploaded", "lab_reports", ["user_id", "uploaded_at"])

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("type", sa.String(50), server_default="info", nullable=False),
        sa.Column("is_read", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("notifications")
    op.drop_table("lab_reports")
    op.drop_table("lab_booking_tests")
    op.drop_table("lab_bookings")
    op.drop_table("laboratory_service_areas")
    op.drop_table("laboratory_tests")
    op.drop_table("laboratories")
