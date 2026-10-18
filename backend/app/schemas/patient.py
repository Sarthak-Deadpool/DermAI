from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PatientCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    age: int = Field(default=None, ge=0, le=120)
    gender : str = Field(min_length=1, max_length=30)
    
class PatientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    age: int | None = Field(default=None, ge=0, le=120)
    gender: str | None = Field(default=None, min_length=1, max_length=30)

class PatientResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id:UUID
    name:str
    age: int
    gender:str
    user_id:UUID | None
    clinician_id:UUID | None
    created_at:datetime