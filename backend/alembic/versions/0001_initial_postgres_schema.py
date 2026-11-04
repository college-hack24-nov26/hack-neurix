"""initial postgres schema (migrated from MongoDB)

Revision ID: 0001
Revises: 
Create Date: 2026-10-25 17:04:48.256588
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # pg_trgm powers fuzzy / substring search on disease, symptom and hospital names.
    # (gen_random_uuid() is built into PostgreSQL 13+, no pgcrypto needed.)
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    op.create_table('doctors',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=150), nullable=False),
    sa.Column('specialization', sa.String(length=100), nullable=False),
    sa.Column('hospital', sa.String(length=200), nullable=True),
    sa.Column('experience', sa.SmallInteger(), nullable=True),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('fee', sa.Integer(), server_default=sa.text('0'), nullable=False),
    sa.Column('languages', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='available', nullable=False),
    sa.CheckConstraint("status IN ('available', 'busy', 'offline')", name='ck_doctors_status'),
    sa.CheckConstraint('fee >= 0', name='ck_doctors_fee'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_index('ix_doctors_specialization', 'doctors', ['specialization'], unique=False)
    op.create_table('hospitals',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('type', sa.String(length=20), nullable=True),
    sa.Column('address', sa.Text(), nullable=True),
    sa.Column('city', sa.String(length=100), nullable=True),
    sa.Column('state', sa.String(length=100), nullable=True),
    sa.Column('pincode', sa.String(length=12), nullable=True),
    sa.Column('phone', sa.String(length=40), nullable=True),
    sa.Column('email', sa.String(length=255), nullable=True),
    sa.Column('website', sa.String(length=500), nullable=True),
    sa.Column('latitude', sa.Float(), nullable=True),
    sa.Column('longitude', sa.Float(), nullable=True),
    sa.Column('specialties', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('rating', sa.Float(), nullable=True),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint('latitude IS NULL OR (latitude BETWEEN -90 AND 90)', name='ck_hospitals_lat'),
    sa.CheckConstraint('longitude IS NULL OR (longitude BETWEEN -180 AND 180)', name='ck_hospitals_lng'),
    sa.CheckConstraint('rating IS NULL OR (rating >= 0 AND rating <= 5)', name='ck_hospitals_rating'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name', 'city', name='uq_hospitals_name_city')
    )
    op.create_index('ix_hospitals_city', 'hospitals', ['city'], unique=False)
    op.create_index('ix_hospitals_lat_lng', 'hospitals', ['latitude', 'longitude'], unique=False)
    op.create_index('ix_hospitals_name_trgm', 'hospitals', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index('ix_hospitals_specialties', 'hospitals', ['specialties'], unique=False, postgresql_using='gin')
    op.create_index('ix_hospitals_type', 'hospitals', ['type'], unique=False)
    op.create_table('organ_systems',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=120), nullable=False),
    sa.Column('slug', sa.String(length=120), nullable=False),
    sa.Column('icon', sa.String(length=16), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('specialist', sa.String(length=120), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name'),
    sa.UniqueConstraint('slug')
    )
    op.create_table('symptoms',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=160), nullable=False),
    sa.Column('slug', sa.String(length=160), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('body_part', sa.String(length=80), nullable=True),
    sa.Column('is_common', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_index('ix_symptoms_is_common', 'symptoms', ['is_common'], unique=False)
    op.create_index('ix_symptoms_name_trgm', 'symptoms', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_table('users',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('first_name', sa.String(length=100), nullable=False),
    sa.Column('last_name', sa.String(length=100), nullable=False),
    sa.Column('email', sa.String(length=255), nullable=False),
    sa.Column('phone', sa.String(length=30), nullable=True),
    sa.Column('password_hash', sa.String(length=255), nullable=False),
    sa.Column('date_of_birth', sa.Date(), nullable=True),
    sa.Column('gender', sa.String(length=20), nullable=True),
    sa.Column('profile_photo', sa.String(length=500), nullable=True),
    sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
    sa.Column('is_active', sa.Boolean(), server_default=sa.text('true'), nullable=False),
    sa.Column('is_verified', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.CheckConstraint("gender IN ('male', 'female', 'other', 'prefer_not')", name='ck_users_gender'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_users_email_lower', 'users', [sa.text('lower(email)')], unique=True)
    op.create_table('chat_sessions',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('title', sa.String(length=200), nullable=True),
    sa.Column('language', sa.String(length=10), server_default='en', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_sessions_user_updated', 'chat_sessions', ['user_id', sa.text('updated_at DESC')], unique=False)
    op.create_table('consultations',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('booking_ref', sa.String(length=40), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('doctor_id', sa.Integer(), nullable=False),
    sa.Column('slot', sa.String(length=60), nullable=False),
    sa.Column('consult_type', sa.String(length=20), server_default='video', nullable=False),
    sa.Column('reason', sa.Text(), nullable=True),
    sa.Column('fee', sa.Integer(), nullable=False),
    sa.Column('status', sa.String(length=20), server_default='confirmed', nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("consult_type IN ('video', 'chat', 'audio')", name='ck_consult_type'),
    sa.CheckConstraint("status IN ('confirmed', 'completed', 'cancelled')", name='ck_consult_status'),
    sa.ForeignKeyConstraint(['doctor_id'], ['doctors.id'], ondelete='RESTRICT'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('booking_ref')
    )
    op.create_index('ix_consultations_user_created', 'consultations', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_table('diseases',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('slug', sa.String(length=220), nullable=False),
    sa.Column('icd_code', sa.String(length=20), nullable=True),
    sa.Column('organ_system_id', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=120), nullable=True),
    sa.Column('severity', sa.String(length=20), nullable=True),
    sa.Column('severity_score', sa.SmallInteger(), nullable=True),
    sa.Column('overview', sa.Text(), nullable=True),
    sa.Column('causes', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('risk_factors', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('complications', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('treatments', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('medications', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('home_remedies', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('prevention', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('precautions', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('specialist', sa.String(length=120), nullable=True),
    sa.Column('specialist_type', sa.String(length=120), nullable=True),
    sa.Column('is_dental', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('search_vector', postgresql.TSVECTOR(), sa.Computed("setweight(to_tsvector('english', coalesce(name, '')), 'A') || setweight(to_tsvector('simple',  coalesce(icd_code, '')), 'A') || setweight(to_tsvector('english', coalesce(overview, '')), 'B')", persisted=True), nullable=True),
    sa.CheckConstraint("severity IN ('Mild', 'Moderate', 'Severe', 'Critical')", name='ck_diseases_severity'),
    sa.ForeignKeyConstraint(['organ_system_id'], ['organ_systems.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('slug')
    )
    op.create_index('ix_diseases_category', 'diseases', ['category'], unique=False)
    op.create_index('ix_diseases_icd_code', 'diseases', ['icd_code'], unique=False)
    op.create_index('ix_diseases_name_trgm', 'diseases', ['name'], unique=False, postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.create_index('ix_diseases_organ_system_id', 'diseases', ['organ_system_id'], unique=False)
    op.create_index('ix_diseases_search_vector', 'diseases', ['search_vector'], unique=False, postgresql_using='gin')
    op.create_table('health_metrics',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('metric_type', sa.String(length=30), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('unit', sa.String(length=20), nullable=True),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('recorded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("metric_type IN ('heart_rate', 'systolic_bp', 'diastolic_bp', 'oxygen_level', 'blood_sugar', 'bmi', 'weight', 'steps', 'temperature')", name='ck_health_metrics_type'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_metrics_user_type_time', 'health_metrics', ['user_id', 'metric_type', sa.text('recorded_at DESC')], unique=False)
    op.create_table('health_records',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=False),
    sa.Column('record_type', sa.String(length=30), server_default='document', nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('file_size', sa.BigInteger(), nullable=True),
    sa.Column('mime_type', sa.String(length=100), nullable=True),
    sa.Column('tags', postgresql.ARRAY(sa.Text()), server_default=sa.text("'{}'"), nullable=False),
    sa.Column('ai_analysis', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('is_analyzed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("record_type IN ('lab_report', 'prescription', 'scan', 'document', 'xray')", name='ck_health_records_type'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_health_records_tags', 'health_records', ['tags'], unique=False, postgresql_using='gin')
    op.create_index('ix_health_records_user_uploaded', 'health_records', ['user_id', sa.text('uploaded_at DESC')], unique=False)
    op.create_table('insurance_policies',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider', sa.String(length=200), nullable=False),
    sa.Column('policy_number', sa.String(length=100), nullable=False),
    sa.Column('policy_type', sa.String(length=50), nullable=True),
    sa.Column('coverage', sa.String(length=100), nullable=True),
    sa.Column('premium', sa.String(length=100), nullable=True),
    sa.Column('renewal_date', sa.Date(), nullable=True),
    sa.Column('status', sa.String(length=20), server_default='active', nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('user_id', 'policy_number', name='uq_policy_user_number')
    )
    op.create_index('ix_insurance_user_created', 'insurance_policies', ['user_id', sa.text('created_at DESC')], unique=False)
    op.create_table('symptom_checks',
    sa.Column('id', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=True),
    sa.Column('symptoms', postgresql.ARRAY(sa.Text()), nullable=False),
    sa.Column('follow_up', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('results', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('ai_powered', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_symptom_checks_user_created', 'symptom_checks', ['user_id', 'created_at'], unique=False)
    op.create_table('chat_messages',
    sa.Column('id', sa.BigInteger(), nullable=False),
    sa.Column('session_id', sa.UUID(), nullable=False),
    sa.Column('role', sa.String(length=20), nullable=False),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.CheckConstraint("role IN ('user', 'assistant', 'system')", name='ck_chat_messages_role'),
    sa.ForeignKeyConstraint(['session_id'], ['chat_sessions.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_chat_messages_session_id', 'chat_messages', ['session_id', 'id'], unique=False)
    op.create_table('disease_symptoms',
    sa.Column('disease_id', sa.Integer(), nullable=False),
    sa.Column('symptom_id', sa.Integer(), nullable=False),
    sa.Column('weight', sa.Float(), server_default=sa.text('1.0'), nullable=False),
    sa.Column('position', sa.SmallInteger(), server_default=sa.text('0'), nullable=False),
    sa.ForeignKeyConstraint(['disease_id'], ['diseases.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['symptom_id'], ['symptoms.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('disease_id', 'symptom_id')
    )
    op.create_index('ix_disease_symptoms_symptom_id', 'disease_symptoms', ['symptom_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_disease_symptoms_symptom_id', table_name='disease_symptoms')
    op.drop_table('disease_symptoms')
    op.drop_index('ix_chat_messages_session_id', table_name='chat_messages')
    op.drop_table('chat_messages')
    op.drop_index('ix_symptom_checks_user_created', table_name='symptom_checks')
    op.drop_table('symptom_checks')
    op.drop_index('ix_insurance_user_created', table_name='insurance_policies')
    op.drop_table('insurance_policies')
    op.drop_index('ix_health_records_user_uploaded', table_name='health_records')
    op.drop_index('ix_health_records_tags', table_name='health_records', postgresql_using='gin')
    op.drop_table('health_records')
    op.drop_index('ix_health_metrics_user_type_time', table_name='health_metrics')
    op.drop_table('health_metrics')
    op.drop_index('ix_diseases_search_vector', table_name='diseases', postgresql_using='gin')
    op.drop_index('ix_diseases_organ_system_id', table_name='diseases')
    op.drop_index('ix_diseases_name_trgm', table_name='diseases', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.drop_index('ix_diseases_icd_code', table_name='diseases')
    op.drop_index('ix_diseases_category', table_name='diseases')
    op.drop_table('diseases')
    op.drop_index('ix_consultations_user_created', table_name='consultations')
    op.drop_table('consultations')
    op.drop_index('ix_chat_sessions_user_updated', table_name='chat_sessions')
    op.drop_table('chat_sessions')
    op.drop_index('uq_users_email_lower', table_name='users')
    op.drop_table('users')
    op.drop_index('ix_symptoms_name_trgm', table_name='symptoms', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.drop_index('ix_symptoms_is_common', table_name='symptoms')
    op.drop_table('symptoms')
    op.drop_table('organ_systems')
    op.drop_index('ix_hospitals_type', table_name='hospitals')
    op.drop_index('ix_hospitals_specialties', table_name='hospitals', postgresql_using='gin')
    op.drop_index('ix_hospitals_name_trgm', table_name='hospitals', postgresql_using='gin', postgresql_ops={'name': 'gin_trgm_ops'})
    op.drop_index('ix_hospitals_lat_lng', table_name='hospitals')
    op.drop_index('ix_hospitals_city', table_name='hospitals')
    op.drop_table('hospitals')
    op.drop_index('ix_doctors_specialization', table_name='doctors')
    op.drop_table('doctors')
