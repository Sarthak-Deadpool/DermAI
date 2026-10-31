"""Build a truthful, on-demand report for the shared model preprocessing transform."""

import base64
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path
from time import perf_counter
from uuid import UUID

import numpy as np
from PIL import Image as PILImage

from app.models.image import Image
from app.schemas.image_preprocessing import (
    ImagePreprocessingResponse,
    PreprocessingOutputResponse,
    PreprocessingSourceResponse,
    PreprocessingStepResponse,
)
from app.services.image_preprocessing import (
    DEFAULT_PREPROCESS_CONFIG,
    PREPROCESS_VERSION,
    preprocess_image,
)


def build_image_preprocessing_report(
    image: Image,
    image_path: str | Path,
) -> ImagePreprocessingResponse:
    """Run the existing deterministic transform and report only observed details.

    The response is generated for this request and is not stored as a processing
    history record. The preview reverses normalization for display only; it is
    not the normalized tensor sent to a model.
    """
    started = perf_counter()
    path = Path(image_path)
    with PILImage.open(path) as source_image:
        source_dimensions = source_image.size
        source_format = source_image.format or image.content_type
        orientation_tag = source_image.getexif().get(274)

    transformed = preprocess_image(path)
    height, width, _ = transformed.shape
    mean = np.asarray(DEFAULT_PREPROCESS_CONFIG.mean, dtype=np.float32).reshape(1, 1, 3)
    std = np.asarray(DEFAULT_PREPROCESS_CONFIG.std, dtype=np.float32).reshape(1, 1, 3)
    display_rgb = np.clip(transformed * std + mean, 0.0, 1.0)
    display_image = PILImage.fromarray(np.rint(display_rgb * 255.0).astype(np.uint8), mode="RGB")
    preview = BytesIO()
    display_image.save(preview, format="PNG", optimize=True)

    config = DEFAULT_PREPROCESS_CONFIG
    output_dimensions = (width, height)
    processing_duration_ms = round((perf_counter() - started) * 1000.0, 3)
    steps = [
        PreprocessingStepResponse(
            name="Decode image",
            description="Opened and decoded the stored, validated image for the shared model transform.",
            status="completed",
            parameters={"source_format": source_format},
            input_dimensions=source_dimensions,
            output_dimensions=source_dimensions,
            input_format=source_format,
            output_format=source_format,
        ),
        PreprocessingStepResponse(
            name="EXIF orientation handling",
            description=(
                "Applied the stored EXIF orientation tag."
                if orientation_tag is not None
                else "Checked EXIF orientation; no orientation tag was present, so no rotation was needed."
            ),
            status="completed",
            parameters={"orientation_tag": orientation_tag, "operation": "Pillow ImageOps.exif_transpose"},
            input_dimensions=source_dimensions,
            output_dimensions=source_dimensions,
            input_format=source_format,
            output_format=source_format,
        ),
        PreprocessingStepResponse(
            name="Convert to RGB",
            description="Converted to RGB; transparent pixels, if present, are composited over white.",
            status="completed",
            parameters={"intermediate_mode": "RGBA", "alpha_background_rgb": [255, 255, 255]},
            input_dimensions=source_dimensions,
            output_dimensions=source_dimensions,
            input_format=source_format,
            output_format="RGB",
        ),
        PreprocessingStepResponse(
            name="Resize and pad",
            description="Applied the shared centered fit/pad transform to the model input size.",
            status="completed",
            parameters={
                "target_size_width_height": list(config.size),
                "resampling": "bilinear",
                "centering": [0.5, 0.5],
                "padding_rgb": list(config.padding_rgb),
            },
            input_dimensions=source_dimensions,
            output_dimensions=output_dimensions,
            input_format="RGB",
            output_format="RGB",
        ),
        PreprocessingStepResponse(
            name="Scale pixel values",
            description="Converted image pixels to float32 and scaled the 0–255 range to 0–1.",
            status="completed",
            parameters={"dtype": "float32", "scale_factor": 1.0 / 255.0},
            input_dimensions=output_dimensions,
            output_dimensions=output_dimensions,
            input_format="RGB uint8",
            output_format="RGB float32 [0,1]",
        ),
        PreprocessingStepResponse(
            name="ImageNet normalization",
            description="Normalized each RGB channel using the shared training/inference configuration.",
            status="completed",
            parameters={"mean": list(config.mean), "std": list(config.std), "layout": config.layout},
            input_dimensions=output_dimensions,
            output_dimensions=output_dimensions,
            input_format="RGB float32 [0,1]",
            output_format="RGB normalized float32",
        ),
    ]

    return ImagePreprocessingResponse(
        image_id=image.id,
        case_id=image.case_id,
        status="completed",
        preprocessing_version=PREPROCESS_VERSION,
        generated_at=datetime.now(timezone.utc),
        processing_duration_ms=processing_duration_ms,
        source=PreprocessingSourceResponse(
            content_type=image.content_type,
            width=source_dimensions[0],
            height=source_dimensions[1],
            file_size=image.file_size,
            sha256=image.sha256,
        ),
        output=PreprocessingOutputResponse(
            width=width,
            height=height,
            format="PNG preview; model tensor is normalized float32",
            channel_order=config.channel_order,
            layout=config.layout,
            dtype=config.dtype,
            normalization=config.scale,
            mean=config.mean,
            std=config.std,
        ),
        preview_data_url=f"data:image/png;base64,{base64.b64encode(preview.getvalue()).decode('ascii')}",
        steps=steps,
    )
