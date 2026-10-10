import re
import uuid
from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, EmailStr, field_validator, model_validator

US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}

NAME_PATTERN = re.compile(r"^[A-Za-z\-']+$")
PHONE_PATTERN = re.compile(r"^\d{10}$")
ZIP_PATTERN = re.compile(r"^\d{5}(-\d{4})?$")


class SexEnum(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    DECLINE = "Decline to Answer"


class PatientCreate(BaseModel):
    first_name: str
    last_name: str
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: EmailStr | None = None
    address_line_1: str
    address_line_2: str | None = None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str = "English"
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str, info) -> str:
        v = v.strip()
        if not 1 <= len(v) <= 50:
            raise ValueError(f"{info.field_name} must be 1-50 characters")
        if not NAME_PATTERN.match(v):
            raise ValueError(f"{info.field_name} must contain only letters, hyphens, and apostrophes")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if not PHONE_PATTERN.match(digits):
            raise ValueError("Must be a valid U.S. 10-digit phone number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str) -> str:
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError("Must be a valid 2-letter U.S. state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str) -> str:
        v = v.strip()
        if not ZIP_PATTERN.match(v):
            raise ValueError("Must be 5-digit or ZIP+4 format (e.g., 12345 or 12345-6789)")
        return v

    @field_validator("city")
    @classmethod
    def validate_city(cls, v: str) -> str:
        v = v.strip()
        if not 1 <= len(v) <= 100:
            raise ValueError("City must be 1-100 characters")
        return v

    @field_validator("address_line_1")
    @classmethod
    def validate_address(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Address is required")
        return v


class PatientUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    date_of_birth: date | None = None
    sex: SexEnum | None = None
    phone_number: str | None = None
    email: EmailStr | None = None
    address_line_1: str | None = None
    address_line_2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    insurance_provider: str | None = None
    insurance_member_id: str | None = None
    preferred_language: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None

    @field_validator("first_name", "last_name")
    @classmethod
    def validate_name(cls, v: str | None, info) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not 1 <= len(v) <= 50:
            raise ValueError(f"{info.field_name} must be 1-50 characters")
        if not NAME_PATTERN.match(v):
            raise ValueError(f"{info.field_name} must contain only letters, hyphens, and apostrophes")
        return v

    @field_validator("date_of_birth")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is None:
            return v
        if v > date.today():
            raise ValueError("Date of birth cannot be in the future")
        return v

    @field_validator("phone_number", "emergency_contact_phone")
    @classmethod
    def validate_phone(cls, v: str | None) -> str | None:
        if v is None:
            return v
        digits = re.sub(r"\D", "", v)
        if not PHONE_PATTERN.match(digits):
            raise ValueError("Must be a valid U.S. 10-digit phone number")
        return digits

    @field_validator("state")
    @classmethod
    def validate_state(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().upper()
        if v not in US_STATES:
            raise ValueError("Must be a valid 2-letter U.S. state abbreviation")
        return v

    @field_validator("zip_code")
    @classmethod
    def validate_zip(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        if not ZIP_PATTERN.match(v):
            raise ValueError("Must be 5-digit or ZIP+4 format")
        return v

    @model_validator(mode="before")
    @classmethod
    def check_at_least_one_field(cls, data: Any) -> Any:
        if isinstance(data, dict) and not any(v is not None for v in data.values()):
            raise ValueError("At least one field must be provided for update")
        return data


class PatientResponse(BaseModel):
    patient_id: uuid.UUID
    first_name: str
    last_name: str
    date_of_birth: date
    sex: SexEnum
    phone_number: str
    email: str | None
    address_line_1: str
    address_line_2: str | None
    city: str
    state: str
    zip_code: str
    insurance_provider: str | None
    insurance_member_id: str | None
    preferred_language: str
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class APIResponse(BaseModel):
    data: Any = None
    error: str | None = None
