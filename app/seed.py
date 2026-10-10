import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient, SexEnum

logger = logging.getLogger(__name__)

SEED_PATIENTS = [
    {
        "first_name": "Jane",
        "last_name": "Doe",
        "date_of_birth": date(1990, 5, 15),
        "sex": SexEnum.FEMALE,
        "phone_number": "5551234567",
        "email": "jane.doe@example.com",
        "address_line_1": "123 Main Street",
        "city": "Miami",
        "state": "FL",
        "zip_code": "33101",
        "preferred_language": "English",
    },
    {
        "first_name": "John",
        "last_name": "Smith",
        "date_of_birth": date(1985, 8, 22),
        "sex": SexEnum.MALE,
        "phone_number": "5559876543",
        "address_line_1": "456 Oak Avenue",
        "address_line_2": "Apt 2B",
        "city": "Orlando",
        "state": "FL",
        "zip_code": "32801",
        "insurance_provider": "Blue Cross Blue Shield",
        "insurance_member_id": "BCBS12345678",
        "preferred_language": "English",
    },
]


async def seed_database(db: AsyncSession) -> None:
    result = await db.execute(select(Patient).limit(1))
    if result.scalar_one_or_none() is not None:
        logger.info("Database already has data, skipping seed")
        return

    for patient_data in SEED_PATIENTS:
        db.add(Patient(**patient_data))

    await db.commit()
    logger.info("Seeded %d demo patients", len(SEED_PATIENTS))
