import sys
from pathlib import Path

import pandas as pd
import pytest
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.audit_dataset_leakage import audit_dataset


def test_audit_separates_patient_bare_lesion_composite_and_exact_hash_overlap(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    image_root = tmp_path / "images"
    image_root.mkdir()
    Image.new("RGB", (12, 12), "red").save(image_root / "train.png")
    (image_root / "test.png").write_bytes((image_root / "train.png").read_bytes())
    Image.new("RGB", (12, 12), "blue").save(image_root / "validation.png")
    pd.DataFrame(
        [
            {"img_id": "train.png", "patient_id": "P1", "lesion_id": "7", "diagnostic": "ACK", "split": "train"},
            {"img_id": "test.png", "patient_id": "P2", "lesion_id": "7", "diagnostic": "BCC", "split": "test"},
            {"img_id": "validation.png", "patient_id": "P3", "lesion_id": "8", "diagnostic": "MEL", "split": "validation"},
        ]
    ).to_csv(manifest_path, index=False)

    report = audit_dataset(manifest_path, image_root)

    assert report["rows"] == 3
    assert report["patient_keys_cross_split"] == 0
    assert report["bare_lesion_ids_cross_split"] == 1
    assert report["patient_lesion_pairs_cross_split"] == 0
    assert report["duplicate_image_hash_groups_cross_split"] == 1
    assert report["missing_images"] == 0
    assert len(report["manifest_sha256"]) == 64


def test_audit_rejects_missing_and_ambiguous_image_files(tmp_path):
    manifest_path = tmp_path / "manifest.csv"
    image_root = tmp_path / "images"
    image_root.mkdir()
    pd.DataFrame(
        [{"img_id": "missing.png", "patient_id": "P1", "lesion_id": "1", "split": "train"}]
    ).to_csv(manifest_path, index=False)
    with pytest.raises(ValueError, match="missing=1"):
        audit_dataset(manifest_path, image_root)

    (image_root / "one").mkdir()
    (image_root / "two").mkdir()
    (image_root / "one" / "missing.png").write_bytes(b"one")
    (image_root / "two" / "missing.png").write_bytes(b"two")
    with pytest.raises(ValueError, match="ambiguous=1"):
        audit_dataset(manifest_path, image_root)
