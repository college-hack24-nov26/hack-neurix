"""
HomeCare+ — Database Seeder (PostgreSQL edition)

Loads everything the app needs to be useful on a fresh database:
organ systems, ~347 diseases, ~940 symptoms (with weights), sample hospitals,
telemedicine doctors and — outside production — a demo user.

Idempotent: safe to run any number of times.
    alembic upgrade head      # create / update the schema first
    python seed_db.py
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import SessionLocal, close_database      # noqa: E402
from app.seeding import seed_all                                   # noqa: E402


async def main() -> None:
    print("\nHomeCare+ Database Seeder (PostgreSQL)")
    print("=" * 42)
    async with SessionLocal() as session:
        async with session.begin():
            counts = await seed_all(session)
    for key, value in counts.items():
        print(f"  {key:<24} {value}")
    if counts["demo_user_created"]:
        print("\n  Demo user created: demo@homecare.plus / Demo@1234")
    print("\nDatabase seeding complete!")
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
