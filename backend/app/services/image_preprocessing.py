from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError


def preprocess_image(
    image_path: str | Path,
    size: tuple[int, int] = (224, 224),

)-> np.ndarray:
    try:
        with Image.open(image_path) as image:
            image = ImageOps.exif_transpose(image)

            image = image.convert("RGB")

            image = image.resize(
                size,
                Image.Resampling.BILINEAR,
            )

            array = np.array(
                image,
                dtype=np.float32,
            ) / np.float32(255.0)

        return array
    except (OSError, ValueError,UnidentifiedImageError):
        raise ValueError(
            "Invalid or corrupted image"
        )from None
