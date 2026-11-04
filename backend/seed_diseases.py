"""
HomeCare+ — Disease library seeder (PostgreSQL edition).

Kept as a separate entry point for backwards compatibility with the old
`python seed_diseases.py` workflow. `seed_db.py` already does the same work
plus hospitals/doctors/demo user, so running both is harmless (idempotent).

The dataset itself now lives in app/data/disease_dataset.py.
"""
import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.config.database import SessionLocal, close_database      # noqa: E402
from app.seeding import _acquire_lock, seed_diseases               # noqa: E402


async def main() -> None:
    print("\nStarting HomeCare+ disease database seeding...\n")
    async with SessionLocal() as session:
        async with session.begin():
            await _acquire_lock(session)
            n_diseases, n_links = await seed_diseases(session)
    print(f"  {n_diseases} diseases in dataset, {n_links} disease-symptom links in database.")
    print("\nDatabase seeding completed successfully!\n")
    await close_database()


if __name__ == "__main__":
    asyncio.run(main())
