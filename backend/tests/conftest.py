"""
Integration tests run against a REAL PostgreSQL database (never the dev one).

    createdb homecare_test
    TEST_DATABASE_URL=postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_test pytest
"""
import asyncio
import os
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
TEST_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+asyncpg://homecare:homecare@localhost:5432/homecare_test"
)
os.environ["DATABASE_URL"] = TEST_URL
os.environ["UPLOAD_DIR"] = tempfile.mkdtemp(prefix="homecare-uploads-")
for k in ("GROQ_API_KEY", "OPENAI_API_KEY", "ANTHROPIC_API_KEY"):
    os.environ[k] = ""          # tests must never call a real LLM
sys.path.insert(0, str(BACKEND))


def _reset_schema():
    import asyncpg

    async def go():
        conn = await asyncpg.connect(TEST_URL.replace("postgresql+asyncpg://", "postgresql://"))
        try:
            await conn.execute("DROP SCHEMA public CASCADE; CREATE SCHEMA public;")
        finally:
            await conn.close()
    asyncio.run(go())


@pytest.fixture(scope="session")
def client():
    _reset_schema()
    subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=BACKEND, check=True,
                   env={**os.environ}, capture_output=True)
    from fastapi.testclient import TestClient
    import main
    with TestClient(main.app) as c:          # startup auto-seeds the empty database
        yield c


def _register(client, email=None):
    email = email or f"user-{uuid.uuid4().hex[:8]}@example.com"
    r = client.post("/api/auth/register", json={
        "firstName": "Test", "lastName": "User", "email": email, "password": "Password123"})
    assert r.status_code == 201, r.text
    return r.json()


@pytest.fixture()
def user(client):
    data = _register(client)
    return {"email": data["user"]["email"], "id": data["user"]["id"],
            "headers": {"Authorization": f"Bearer {data['token']}"}}


@pytest.fixture()
def other_user(client):
    data = _register(client)
    return {"headers": {"Authorization": f"Bearer {data['token']}"}}


def db_run(fn):
    """Run `await fn(session)` on a private connection (never shares the app's pool/event loop)."""
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
    from sqlalchemy.pool import NullPool

    async def go():
        engine = create_async_engine(TEST_URL, poolclass=NullPool)
        try:
            async with AsyncSession(engine, expire_on_commit=False) as s:
                return await fn(s)
        finally:
            await engine.dispose()
    return asyncio.run(go())
