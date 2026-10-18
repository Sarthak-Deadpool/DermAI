import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    patient_id: uuid.UUID
    case_label: str | None = Field(default=None, max_length=100)
    description: str | None = None
    body_location: str | None = Field(default=None, max_length=100)
    image_source: str | None = Field(default=None, max_length=50)
    
class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    owner_user_id: uuid.UUID
    patient_id: uuid.UUID
    case_label: str | None
    description: str | None
    body_location: str | None
    image_source: str | None
    status: str
    created_at: datetime
