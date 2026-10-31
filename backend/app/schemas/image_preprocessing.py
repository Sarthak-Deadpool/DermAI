from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PreprocessingStepResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    description: str
    status: Literal["completed"]
    parameters: dict[str, Any]
    input_dimensions: tuple[int, int] | None = None
    output_dimensions: tuple[int, int] | None = None
    input_format: str | None = None
    output_format: str | None = None


class PreprocessingSourceResponse(BaseModel):
    content_type: str
    width: int | None
    height: int | None
    file_size: int
    sha256: str | None


class PreprocessingOutputResponse(BaseModel):
    width: int
    height: int
    format: str
    channel_order: str
    layout: str
    dtype: str
    normalization: str
    mean: tuple[float, float, float]
    std: tuple[float, float, float]


class ImagePreprocessingResponse(BaseModel):
    image_id: UUID
    case_id: UUID
    status: Literal["completed"]
    preprocessing_version: str
    generated_at: datetime
    processing_duration_ms: float
    history_persisted: Literal[False] = False
    source: PreprocessingSourceResponse
    output: PreprocessingOutputResponse
    preview_data_url: str
    steps: list[PreprocessingStepResponse]
