import uuid
from datetime import date, datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Patient
from app.schemas import PatientCreate, PatientUpdate


async def create_patient(db: AsyncSession, data: PatientCreate) -> Patient:
    patient = Patient(**data.model_dump())
    db.add(patient)
    await db.commit()
    await db.refresh(patient)
    return patient


async def get_patient(db: AsyncSession, patient_id: uuid.UUID) -> Patient | None:
    stmt = select(Patient).where(
        Patient.patient_id == patient_id,
        Patient.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def list_patients(
    db: AsyncSession,
    last_name: str | None = None,
    date_of_birth: date | None = None,
    phone_number: str | None = None,
) -> list[Patient]:
    stmt = select(Patient).where(Patient.deleted_at.is_(None))
    if last_name:
        stmt = stmt.where(Patient.last_name.ilike(f"%{last_name}%"))
    if date_of_birth:
        stmt = stmt.where(Patient.date_of_birth == date_of_birth)
    if phone_number:
        stmt = stmt.where(Patient.phone_number == phone_number)
    stmt = stmt.order_by(Patient.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def update_patient(
    db: AsyncSession, patient_id: uuid.UUID, data: PatientUpdate
) -> Patient | None:
    patient = await get_patient(db, patient_id)
    if not patient:
        return None
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(patient, field, value)
    await db.commit()
    await db.refresh(patient)
    return patient


async def soft_delete_patient(db: AsyncSession, patient_id: uuid.UUID) -> Patient | None:
    patient = await get_patient(db, patient_id)
    if not patient:
        return None
    patient.deleted_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(patient)
    return patient


async def find_patient_by_phone(db: AsyncSession, phone_number: str) -> Patient | None:
    stmt = select(Patient).where(
        Patient.phone_number == phone_number,
        Patient.deleted_at.is_(None),
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()
