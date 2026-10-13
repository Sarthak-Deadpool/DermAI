
import numpy as np
import pytest
from PIL import Image

from app.services.image_preprocessing import preprocess_image


def test_preprocess_uploaded_image():
    image_path = (
        "uploads/2c2fe58f-021e-44bd-8f47-9c4d633d5999/"
        "3d5ccafd215e45f8beafba70b953a642.png"
    )

    result = preprocess_image(image_path)

    assert result.shape == (224, 224, 3)
    assert result.dtype == np.float32
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_corrupted_image_raises_error(tmp_path):
    image_path = tmp_path / "corrupted.png"
    image_path.write_bytes(b"not a real image")

    with pytest.raises(ValueError, match="Invalid or corrupted image"):
        preprocess_image(image_path)


@pytest.mark.parametrize(
    "mode,color",
    [
        ("L", 128),
        ("RGBA", (0, 255, 0, 128)),
    ],
)
def test_preprocess_grayscale_and_rgba(tmp_path, mode, color):
    image_path = tmp_path / "sample.png"
    Image.new(mode, (320, 180), color).save(image_path)

    result = preprocess_image(image_path)

    assert result.shape == (224, 224, 3)
    assert result.dtype == np.float32
    assert result.min() >= 0.0
    assert result.max() <= 1.0


def test_original_image_remains_unchanged(tmp_path):
    image_path = tmp_path / "original.png"
    Image.new("RGB", (320, 180), "red").save(image_path)
    original_bytes = image_path.read_bytes()

    preprocess_image(image_path)

    assert image_path.read_bytes() == original_bytes
