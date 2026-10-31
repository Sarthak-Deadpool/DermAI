
import numpy as np
import pytest
from PIL import Image

from app.services.image_preprocessing import (
    DEFAULT_PREPROCESS_CONFIG,
    preprocess_image,
)


def test_preprocess_uploaded_image(tmp_path):
    image_path = tmp_path / "uploaded_sample.png"
    Image.new("RGB", (320, 180), "blue").save(image_path)

    result = preprocess_image(image_path)

    assert result.shape == (224, 224, 3)
    assert result.dtype == np.float32
    assert np.isfinite(result).all()
    assert result.min() < 0.0


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
    assert np.isfinite(result).all()


def test_original_image_remains_unchanged(tmp_path):
    image_path = tmp_path / "original.png"
    Image.new("RGB", (320, 180), "red").save(image_path)
    original_bytes = image_path.read_bytes()

    preprocess_image(image_path)

    assert image_path.read_bytes() == original_bytes


def test_imagenet_normalization_contract(tmp_path):
    image_path = tmp_path / "constant.png"
    Image.new("RGB", (224, 224), (128, 128, 128)).save(image_path)

    result = preprocess_image(image_path)
    expected = (
        np.float32(128 / 255) - np.asarray(DEFAULT_PREPROCESS_CONFIG.mean)
    ) / np.asarray(DEFAULT_PREPROCESS_CONFIG.std)

    np.testing.assert_allclose(result[112, 112], expected, rtol=0, atol=1e-6)


@pytest.mark.parametrize("orientation", range(1, 9))
def test_all_exif_orientations_match_physically_oriented_image(
    tmp_path, orientation
):
    from PIL import ImageOps

    base = Image.new("RGB", (5, 3))
    base.putdata([(x * 40, y * 70, (x + y) * 20) for y in range(3) for x in range(5)])
    oriented_path = tmp_path / f"exif-{orientation}.png"
    expected_path = tmp_path / f"expected-{orientation}.png"
    exif = Image.Exif()
    exif[274] = orientation
    base.save(oriented_path, exif=exif)
    operations = {
        1: None,
        2: Image.Transpose.FLIP_LEFT_RIGHT,
        3: Image.Transpose.ROTATE_180,
        4: Image.Transpose.FLIP_TOP_BOTTOM,
        5: Image.Transpose.TRANSPOSE,
        6: Image.Transpose.ROTATE_270,
        7: Image.Transpose.TRANSVERSE,
        8: Image.Transpose.ROTATE_90,
    }
    expected = base if operations[orientation] is None else base.transpose(operations[orientation])
    expected.save(expected_path)

    np.testing.assert_allclose(
        preprocess_image(oriented_path), preprocess_image(expected_path),
        rtol=0, atol=0,
    )


def test_training_and_api_preprocessing_are_identical_without_augmentation(tmp_path):
    import sys
    from pathlib import Path

    torch = pytest.importorskip("torch")
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from scripts.dermai_dataset import preprocess_dataset_image

    image_path = tmp_path / "parity.png"
    Image.new("RGB", (79, 121), (37, 119, 203)).save(image_path)
    expected = torch.from_numpy(preprocess_image(image_path)).permute(2, 0, 1)

    actual = preprocess_dataset_image(image_path, augment=False)

    torch.testing.assert_close(actual, expected, rtol=0, atol=0)
