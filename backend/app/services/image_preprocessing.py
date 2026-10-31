from pathlib import Path
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError
from app.core.config import settings



MAX_IMAGE_PIXELS = settings.MAX_IMAGE_PIXELS
PREPROCESS_VERSION = "m1.2-imagenet-rgb224"


@dataclass(frozen=True)
class PreprocessConfig:
    size: tuple[int, int] = (224, 224)
    channel_order: str = "RGB"
    layout: str = "HWC"
    dtype: str = "float32"
    scale: str = "0_1_then_imagenet_mean_std"
    mean: tuple[float, float, float] = (0.485, 0.456, 0.406)
    std: tuple[float, float, float] = (0.229, 0.224, 0.225)
    padding_rgb: tuple[int, int, int] = (0, 0, 0)


DEFAULT_PREPROCESS_CONFIG = PreprocessConfig()

def preprocess_image(
    image_path: str | Path,
    size: tuple[int, int] | None = None,
    *,
    config: PreprocessConfig = DEFAULT_PREPROCESS_CONFIG,

)-> np.ndarray:
    
    target_size = size or config.size
    if target_size[0] <= 0 or target_size[1] <= 0:
        raise ValueError("Image dimensions must be positive")
    
    
    
    try:
        with Image.open(image_path) as source:
            
            image = ImageOps.exif_transpose(source)
            
            
            width, height = image.size
            
            
            if width <=0 or height <= 0:
                raise ValueError("Invalid image dimensions")
            
            
            if width*height > MAX_IMAGE_PIXELS:
                raise ValueError("Image dimensions are too large")

            image = image.convert("RGBA")
            background = Image.new("RGBA", image.size, (255, 255, 255, 255))
            image = Image.alpha_composite(background, image).convert("RGB")
            image = ImageOps.pad(
                image,
                target_size,
                method=Image.Resampling.BILINEAR,
                color=config.padding_rgb,
                centering=(0.5, 0.5),
            )

            array = np.array(
                image,
                dtype=np.float32,
            ) / np.float32(255.0)
            mean = np.asarray(config.mean, dtype=np.float32).reshape(1, 1, 3)
            std = np.asarray(config.std, dtype=np.float32).reshape(1, 1, 3)
            array = (array - mean) / std

        return array
    
    except (OSError, ValueError,UnidentifiedImageError) as exc:
        raise ValueError(
            "Invalid or corrupted image"
        )from exc
