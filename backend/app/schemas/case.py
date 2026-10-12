import uuid

from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field


class CaseCreate(BaseModel):
    case_label: str | None = Field(default=None, max_length=100)
    body_location: str | None = Field(default=None, max_length=100)
    image_source: str | None = Field(default=None, max_length=50)
    
class CaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: uuid.UUID
    owner_user_id: uuid.UUID
    case_label: str | None
    body_location: str | None
    image_source: str | None
    status: str
    created_at: datetime
