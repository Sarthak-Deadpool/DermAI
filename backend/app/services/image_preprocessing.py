from pathlib import Path

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError



MAX_IMAGE_PIXELS = 25_000_000

def preprocess_image(
    image_path: str | Path,
    size: tuple[int, int] = (224, 224),

)-> np.ndarray:
    
    if size[0] <= 0 or size[1] <= 0:
        raise ValueError("Image dimensions must be positive")
    
    
    
    try:
        with Image.open(image_path) as source:
            
            image = ImageOps.exif_transpose(source)
            
            
            width, height = image.size
            
            
            if width <=0 or height <= 0:
                raise ValueError("Invalid image dimensions")
            
            
            if width*height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large")

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
    
    except (OSError, ValueError,UnidentifiedImageError) as exc:
        raise ValueError(
            "Invalid or corrupted image"
        )from exc
