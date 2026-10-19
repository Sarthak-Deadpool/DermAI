
import torch
from torch.utils.data import DataLoader

from scripts.dermai_dataset import (
    CLASS_TO_IDX,
    DermAIDataset,
    DEFAULT_MANIFEST,
    DEFAULT_IMAGE_ROOT,
    validate_manifest,
)
import pandas as pd


def test_manifest_integrity():
    manifest = pd.read_csv(DEFAULT_MANIFEST)
    validate_manifest(manifest)

    assert len(manifest) == 2271
    assert set(manifest["diagnostic"]) == set(CLASS_TO_IDX)
    assert set(manifest["split"]) == {"train", "validation", "test"}


def test_patient_separation():
    manifest = pd.read_csv(DEFAULT_MANIFEST)

    patient_splits = manifest.groupby("patient_id")["split"].nunique()
    assert (patient_splits == 1).all()


def test_real_image_and_label():
    dataset = DermAIDataset(
        split="train",
        manifest_path=DEFAULT_MANIFEST,
        image_root=DEFAULT_IMAGE_ROOT,
    )

    image, label = dataset[0]

    assert image.shape == (3, 224, 224)
    assert image.dtype == torch.float32
    assert torch.isfinite(image).all()
    assert image.min() >= 0
    assert image.max() <= 1
    assert label.dtype == torch.long
    assert 0 <= label.item() < len(CLASS_TO_IDX)


def test_batch_shapes():
    dataset = DermAIDataset(
        split="train",
        manifest_path=DEFAULT_MANIFEST,
        image_root=DEFAULT_IMAGE_ROOT,
    )
    loader = DataLoader(dataset, batch_size=2, shuffle=False)

    images, labels = next(iter(loader))

    assert images.shape == (2, 3, 224, 224)
    assert labels.shape == (2,)
