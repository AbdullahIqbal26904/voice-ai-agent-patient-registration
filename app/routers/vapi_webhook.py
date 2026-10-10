import logging
from typing import Any

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas import PatientCreate
from app.services import patient_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/vapi", tags=["vapi"])


@router.post("/tool-call")
async def handle_tool_call(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    message = body.get("message", {})
    tool_call_list = message.get("toolCallList", [])

    results = []
    for tool_call in tool_call_list:
        tool_name = tool_call.get("function", {}).get("name", "")
        arguments = tool_call.get("function", {}).get("arguments", {})
        tool_call_id = tool_call.get("id", "")

        logger.info("Vapi tool call: %s with args: %s", tool_name, arguments)

        try:
            if tool_name == "save_patient":
                result = await _handle_save_patient(db, arguments)
            elif tool_name == "lookup_patient_by_phone":
                result = await _handle_lookup_patient(db, arguments)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}
        except Exception as e:
            logger.exception("Tool call failed: %s", tool_name)
            result = {"error": str(e)}

        results.append({
            "toolCallId": tool_call_id,
            "result": str(result),
        })

    return {"results": results}


async def _handle_save_patient(db: AsyncSession, args: dict[str, Any]) -> dict:
    phone = args.get("phone_number", "")
    if phone:
        import re
        phone = re.sub(r"\D", "", phone)
        args["phone_number"] = phone

    emergency_phone = args.get("emergency_contact_phone")
    if emergency_phone:
        import re
        emergency_phone = re.sub(r"\D", "", emergency_phone)
        args["emergency_contact_phone"] = emergency_phone

    existing = await patient_service.find_patient_by_phone(db, phone) if phone else None
    if existing:
        return {
            "status": "duplicate_found",
            "patient_id": str(existing.patient_id),
            "first_name": existing.first_name,
            "last_name": existing.last_name,
            "message": f"A patient named {existing.first_name} {existing.last_name} already exists with this phone number.",
        }

    patient_data = PatientCreate(**args)
    patient = await patient_service.create_patient(db, patient_data)
    logger.info("Patient created: %s %s (ID: %s)", patient.first_name, patient.last_name, patient.patient_id)
    return {
        "status": "success",
        "patient_id": str(patient.patient_id),
        "message": f"Patient {patient.first_name} {patient.last_name} has been successfully registered.",
    }


async def _handle_lookup_patient(db: AsyncSession, args: dict[str, Any]) -> dict:
    phone = args.get("phone_number", "")
    if phone:
        import re
        phone = re.sub(r"\D", "", phone)

    patient = await patient_service.find_patient_by_phone(db, phone)
    if patient:
        return {
            "status": "found",
            "patient_id": str(patient.patient_id),
            "first_name": patient.first_name,
            "last_name": patient.last_name,
            "message": f"Found existing patient: {patient.first_name} {patient.last_name}.",
        }
    return {
        "status": "not_found",
        "message": "No existing patient found with this phone number.",
    }
