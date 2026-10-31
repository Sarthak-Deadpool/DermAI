from pathlib import Path

import pytest
from fastapi import HTTPException

from app.services.image_storage import resolve_upload_path


def test_resolve_upload_path_accepts_only_paths_inside_root(tmp_path):
    root = tmp_path / "private-uploads"
    root.mkdir()
    image = root / "case" / "image.jpg"
    image.parent.mkdir()
    image.write_bytes(b"test")

    assert resolve_upload_path(image, root) == image.resolve()
    assert resolve_upload_path("case/image.jpg", root) == image.resolve()

    with pytest.raises(HTTPException) as exc:
        resolve_upload_path(root / ".." / "outside.jpg", root)
    assert exc.value.status_code == 404
    assert exc.value.detail == "Image not found"


def test_resolve_upload_path_rejects_symlink_escape(tmp_path):
    root = tmp_path / "private-uploads"
    root.mkdir()
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(b"not an image")
    link = root / "linked.jpg"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"Symlink creation is unavailable in this environment: {exc}")

    with pytest.raises(HTTPException) as exc:
        resolve_upload_path(link, root)
    assert exc.value.status_code == 404
