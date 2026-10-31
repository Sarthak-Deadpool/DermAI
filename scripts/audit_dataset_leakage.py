"""Reproducibly summarize patient/lesion split overlap and exact image hashes."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets" / "split_manifest.csv"
IMAGE_ROOT = ROOT / "datasets" / "zr7vgbcyr2-1" / "images"


def audit_dataset(manifest_path: Path = MANIFEST, image_root: Path = IMAGE_ROOT) -> dict:
    manifest_path = Path(manifest_path)
    image_root = Path(image_root)
    manifest_bytes = manifest_path.read_bytes()
    frame = pd.read_csv(
        manifest_path,
        dtype={"img_id": str, "patient_id": str, "lesion_id": str, "split": str},
    )
    required = {"img_id", "patient_id", "lesion_id", "split"}
    if not required <= set(frame.columns):
        raise ValueError(f"Manifest missing fields: {sorted(required - set(frame.columns))}")
    if frame[list(required)].isna().any().any():
        raise ValueError("Manifest has null identifiers or split values")

    files_by_name: dict[str, list[Path]] = defaultdict(list)
    for path in image_root.rglob("*"):
        if path.is_file():
            files_by_name[path.name].append(path)

    image_hashes: dict[str, str] = {}
    missing_images: list[str] = []
    ambiguous_images: list[str] = []
    for image_id in frame["img_id"]:
        candidates = files_by_name.get(image_id, [])
        if len(candidates) == 0:
            missing_images.append(image_id)
        elif len(candidates) != 1:
            ambiguous_images.append(image_id)
        else:
            image_hashes[image_id] = hashlib.sha256(candidates[0].read_bytes()).hexdigest()
    if missing_images or ambiguous_images:
        raise ValueError(
            f"Image resolution failed: missing={len(missing_images)}, ambiguous={len(ambiguous_images)}"
        )

    def cross_split_count(key_columns: list[str]) -> int:
        counts = frame.groupby(key_columns, dropna=False)["split"].nunique()
        return int((counts > 1).sum())

    hash_splits: dict[str, set[str]] = defaultdict(set)
    for row in frame[["img_id", "split"]].itertuples(index=False):
        hash_splits[image_hashes[row.img_id]].add(row.split)

    return {
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "rows": len(frame),
        "patient_count": int(frame["patient_id"].nunique()),
        "unique_bare_lesion_ids": int(frame["lesion_id"].nunique()),
        "unique_patient_lesion_pairs": int(frame[["patient_id", "lesion_id"]].drop_duplicates().shape[0]),
        "patient_keys_cross_split": cross_split_count(["patient_id"]),
        "bare_lesion_ids_cross_split": cross_split_count(["lesion_id"]),
        "patient_lesion_pairs_cross_split": cross_split_count(["patient_id", "lesion_id"]),
        "missing_images": len(missing_images),
        "duplicate_image_hash_groups_cross_split": sum(len(splits) > 1 for splits in hash_splits.values()),
        "near_duplicate_method": None,
    }


def main() -> None:
    report = audit_dataset()
    print(json.dumps(report, indent=2, sort_keys=True))
    if report["patient_keys_cross_split"] or report["patient_lesion_pairs_cross_split"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
