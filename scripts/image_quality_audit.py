
from pathlib import Path
import json

import numpy as np
import pandas as pd
from PIL import Image, ImageOps, UnidentifiedImageError

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "datasets" / "split_manifest.csv"
IMAGE_ROOT = ROOT / "datasets" / "zr7vgbcyr2-1" / "images"
OUTPUT = ROOT / "datasets" / "image_quality_audit.csv"
SUMMARY = ROOT / "datasets" / "image_quality_audit_summary.txt"

# Screening thresholds only; these are not clinical quality standards.
MIN_DIMENSION = 100
BLUR_VARIANCE_THRESHOLD = 50.0


def resolve_image(img_id):
    """Find an image by its filename under the configured image root."""
    filename = Path(str(img_id)).name

    # The manifest already contains the extension, e.g. image.png.
    direct_matches = [
        p for p in IMAGE_ROOT.rglob(filename)
        if p.is_file()
    ]

    if len(direct_matches) != 1:
        status = "missing_path" if not direct_matches else "ambiguous_path"
        return None, status

    return direct_matches[0], "ok"


def main():
    manifest = pd.read_csv(MANIFEST)

    required = {"img_id", "patient_id", "diagnostic", "split"}
    missing_columns = required - set(manifest.columns)
    if missing_columns:
        raise ValueError(f"Manifest is missing columns: {sorted(missing_columns)}")

    records = []

    for row in manifest.itertuples(index=False):
        path, path_status = resolve_image(str(row.img_id))

        record = {
            "img_id": row.img_id,
            "patient_id": row.patient_id,
            "diagnostic": row.diagnostic,
            "split": row.split,
            "path_status": path_status,
            "width": None,
            "height": None,
            "aspect_ratio": None,
            "mode": None,
            "mean_brightness": None,
            "brightness_std": None,
            "laplacian_variance": None,
            "small_image_flag": None,
            "potential_blur_flag": None,
            "error": None,
        }

        if path is not None:
            try:
                with Image.open(path) as source:
                    image = ImageOps.exif_transpose(source)
                    image.load()

                    width, height = image.size
                    rgb = image.convert("RGB")
                    gray = np.asarray(rgb.convert("L"), dtype=np.float32)

                    # Discrete Laplacian variance: a rough blur-screening heuristic.
                    laplacian = (
                        -4 * gray[1:-1, 1:-1]
                        + gray[:-2, 1:-1]
                        + gray[2:, 1:-1]
                        + gray[1:-1, :-2]
                        + gray[1:-1, 2:]
                    )
                    blur_score = (
                        float(laplacian.var())
                        if min(gray.shape) >= 3
                        else None
                    )

                    record.update({
                        "width": width,
                        "height": height,
                        "aspect_ratio": width / height if height else None,
                        "mode": source.mode,
                        "mean_brightness": float(gray.mean()),
                        "brightness_std": float(gray.std()),
                        "laplacian_variance": blur_score,
                        "small_image_flag": min(width, height) < MIN_DIMENSION,
                        "potential_blur_flag": (
                            blur_score < BLUR_VARIANCE_THRESHOLD
                            if blur_score is not None
                            else None
                        ),
                    })
            except (OSError, ValueError, UnidentifiedImageError) as exc:
                record["path_status"] = "unreadable"
                record["error"] = type(exc).__name__

        records.append(record)

    results = pd.DataFrame(records)
    results.to_csv(OUTPUT, index=False)

    summary = {
        "manifest_rows": len(manifest),
        "audited_rows": len(results),
        "path_status_counts": results["path_status"].value_counts(
            dropna=False
        ).to_dict(),
        "small_image_count": int(results["small_image_flag"].eq(True).sum()),
        "potential_blur_count": int(
            results["potential_blur_flag"].eq(True).sum()
        ),
        "unreadable_count": int(results["path_status"].eq("unreadable").sum()),
        "by_split": results.groupby("split", dropna=False).agg(
            images=("img_id", "count"),
            small_images=("small_image_flag", lambda s: int(s.eq(True).sum())),
            potential_blur=("potential_blur_flag", lambda s: int(s.eq(True).sum())),
            unreadable=("path_status", lambda s: int(s.eq("unreadable").sum())),
        ).to_dict(orient="index"),
    }

    SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"CSV report: {OUTPUT}")
    print(f"Summary:    {SUMMARY}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
