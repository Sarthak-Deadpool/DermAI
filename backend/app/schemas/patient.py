from datetime import datetime
from uuid import UUID

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.core.privacy import reject_obvious_identifiers


Gender = Literal["female", "male", "non_binary", "other", "prefer_not_to_say", "unknown"]
FitzpatrickType = Literal["I", "II", "III", "IV", "V", "VI"]
class PatientCreate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=1, max_length=150)
    age: int = Field(ge=0, le=120)
    gender: Gender = "prefer_not_to_say"
    medical_history: str | None = Field(default=None, max_length=2000)
    known_allergies: str | None = Field(default=None, max_length=1000)
    fitzpatrick_type: FitzpatrickType | None = None

    @field_validator("medical_history", "known_allergies")
    @classmethod
    def validate_deidentified_text(cls, value: str | None) -> str | None:
        return reject_obvious_identifiers(value)

    @field_validator("patient_name")
    @classmethod
    def normalize_patient_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Patient name cannot be blank.")
        return cleaned
    
class PatientUpdate(BaseModel):
    patient_name: str | None = Field(default=None, min_length=1, max_length=150)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: Gender | None = None
    medical_history: str | None = Field(default=None, max_length=2000)
    known_allergies: str | None = Field(default=None, max_length=1000)
    fitzpatrick_type: FitzpatrickType | None = None

    @field_validator("medical_history", "known_allergies")
    @classmethod
    def validate_deidentified_text(cls, value: str | None) -> str | None:
        return reject_obvious_identifiers(value)

    @field_validator("patient_name")
    @classmethod
    def normalize_patient_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Patient name cannot be blank.")
        return cleaned

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id:UUID
    patient_code: str
    patient_name: str | None
    age: int
    gender:str
    medical_history: str | None
    known_allergies: str | None
    fitzpatrick_type: str | None
    user_id:UUID | None
    clinician_id:UUID | None
    archived_at: datetime | None
    created_at:datetime
