import uuid

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.privacy import reject_obvious_identifiers


class CaseCreate(BaseModel):
    patient_id: uuid.UUID
    case_label: str | None = Field(default=None, max_length=100)
    description: str | None = None
    body_location: str | None = Field(default=None, max_length=100)
    image_source: str | None = Field(default=None, max_length=50)
    capture_date: datetime | None = None

    @field_validator("description")
    @classmethod
    def validate_deidentified_description(cls, value: str | None) -> str | None:
        return reject_obvious_identifiers(value)
    
class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    owner_user_id: uuid.UUID
    patient_id: uuid.UUID
    case_label: str | None
    description: str | None
    body_location: str | None
    image_source: str | None
    capture_date: datetime | None
    status: str
    created_at: datetime


class CaseStatusUpdate(BaseModel):
    status: Literal["image_uploaded", "quality_assessed", "analysis_pending", "analyzed", "failed"]


class CaseNoteCreate(BaseModel):
    note: str = Field(min_length=1, max_length=4000)

    @field_validator("note")
    @classmethod
    def validate_deidentified_note(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Note cannot be empty.")
        return reject_obvious_identifiers(value) or value


class CaseNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_id: uuid.UUID
    author_user_id: uuid.UUID
    note: str
    created_at: datetime


class CaseEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    case_id: uuid.UUID
    actor_user_id: uuid.UUID
    event_type: str
    created_at: datetime
