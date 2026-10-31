"""Best-effort, retryable file compensation and upload-storage reconciliation."""

import logging
import time
from pathlib import Path
from typing import Iterable

from app.models.image import Image
from app.services.image_storage import resolve_upload_path


logger = logging.getLogger(__name__)


def cleanup_uploaded_file(
    path: Path,
    *,
    attempts: int = 3,
    retry_delay_seconds: float = 0.05,
) -> bool:
    """Remove a just-written upload with bounded retries.

    The original database exception must remain the caller's exception. A
    persistent filesystem failure is logged using only the random storage
    filename, then left for the read-only reconciliation command to detect.
    """
    for attempt in range(1, attempts + 1):
        try:
            path.unlink(missing_ok=True)
            return True
        except OSError as exc:
            if attempt == attempts:
                logger.error(
                    "Upload compensation failed; storage reconciliation required",
                    extra={
                        "storage_filename": path.name,
                        "attempts": attempts,
                        "error_type": type(exc).__name__,
                    },
                )
                return False
            time.sleep(retry_delay_seconds)
    return False


def inspect_upload_storage(images: Iterable[Image], storage_root: Path) -> dict:
    """Return missing DB-backed files, unsafe DB paths, and orphan files.

    This is intentionally report-only. Deletion requires a separate retention
    policy and human review because image files may contain sensitive data.
    """
    root = Path(storage_root).resolve()
    image_rows = list(images)
    referenced_paths: set[Path] = set()
    missing_image_ids: list[str] = []
    unsafe_image_ids: list[str] = []

    for image in image_rows:
        try:
            resolved = resolve_upload_path(image.file_path, root)
        except Exception:
            unsafe_image_ids.append(str(image.id))
            continue
        referenced_paths.add(resolved)
        if not resolved.is_file():
            missing_image_ids.append(str(image.id))

    orphan_files = []
    if root.is_dir():
        for candidate in root.rglob("*"):
            if candidate.is_symlink() or not candidate.is_file():
                continue
            if candidate.suffix.lower() not in {".png", ".jpg", ".jpeg"}:
                continue
            resolved = candidate.resolve()
            if resolved not in referenced_paths:
                orphan_files.append(candidate.relative_to(root).as_posix())

    return {
        "database_image_rows": len(image_rows),
        "missing_file_image_ids": sorted(missing_image_ids),
        "unsafe_path_image_ids": sorted(unsafe_image_ids),
        "orphan_files": sorted(orphan_files),
    }
