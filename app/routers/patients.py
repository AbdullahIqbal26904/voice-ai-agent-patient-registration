import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import APIResponse, PatientCreate, PatientResponse, PatientUpdate
from app.services import patient_service

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=APIResponse)
async def list_patients(
    last_name: str | None = Query(None),
    date_of_birth: date | None = Query(None),
    phone_number: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
):
    patients = await patient_service.list_patients(
        db, last_name=last_name, date_of_birth=date_of_birth, phone_number=phone_number
    )
    return APIResponse(data=[PatientResponse.model_validate(p) for p in patients])


@router.get("/{patient_id}", response_model=APIResponse)
async def get_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    patient = await patient_service.get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return APIResponse(data=PatientResponse.model_validate(patient))


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(
    data: PatientCreate,
    db: AsyncSession = Depends(get_db),
):
    patient = await patient_service.create_patient(db, data)
    return APIResponse(data=PatientResponse.model_validate(patient))


@router.put("/{patient_id}", response_model=APIResponse)
async def update_patient(
    patient_id: uuid.UUID,
    data: PatientUpdate,
    db: AsyncSession = Depends(get_db),
):
    patient = await patient_service.update_patient(db, patient_id, data)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return APIResponse(data=PatientResponse.model_validate(patient))


@router.delete("/{patient_id}", response_model=APIResponse)
async def delete_patient(
    patient_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    patient = await patient_service.soft_delete_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return APIResponse(data={"message": "Patient record deleted"})
