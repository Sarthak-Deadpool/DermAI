from unittest.mock import patch
from uuid import UUID
from pathlib import Path

import pytest
from fastapi import UploadFile
from io import BytesIO

from app.models.case import Case
from app.services.image_service import upload_case_image
from app.services.image_cleanup import inspect_upload_storage


def test_database_failure_removes_saved_file(tmp_path):
    case_id = UUID("2c2fe58f-021e-44bd-8f47-9c4d633d5999")
    owner_id = UUID("da1a4637-89aa-4316-87e6-b69fa27bce6f")

    # Fake case owned by the test user
    case = Case()
    case.id = case_id
    case.owner_user_id = owner_id

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return case

    class FakeDB:
        def query(self, model):
            return FakeQuery()

        def rollback(self):
            pass

    # Use a valid PNG at the configured minimum side so the test reaches the
    # simulated database failure rather than failing image validation first.
    from PIL import Image as PILImage

    image_bytes = BytesIO()
    PILImage.new("RGB", (100, 100), "red").save(image_bytes, format="PNG")
    image_bytes.seek(0)

    upload = UploadFile(
        filename="test.png",
        file=image_bytes,
        headers={"content-type": "image/png"},
    )

    with patch(
        "app.services.image_service.UPLOAD_DIR",
        tmp_path,
    ), patch(
        "app.services.image_service.create_image",
        side_effect=RuntimeError("Simulated database failure"),
    ):
        with pytest.raises(RuntimeError, match="Simulated database failure"):
            upload_case_image(
                db=FakeDB(),
                case_id=case_id,
                owner_user_id=owner_id,
                file=upload,
            )

    # The image must not remain on disk after DB failure.
    assert list(tmp_path.rglob("*.png")) == []


def test_persistent_cleanup_failure_preserves_db_error_and_is_detectable(
    tmp_path, monkeypatch, caplog
):
    from PIL import Image as PILImage

    case_id = UUID("2c2fe58f-021e-44bd-8f47-9c4d633d5999")
    owner_id = UUID("da1a4637-89aa-4316-87e6-b69fa27bce6f")
    case = Case()
    case.id = case_id
    case.owner_user_id = owner_id

    class FakeQuery:
        def filter(self, *args, **kwargs):
            return self

        def first(self):
            return case

    class FakeDB:
        rolled_back = False

        def query(self, model):
            return FakeQuery()

        def rollback(self):
            self.rolled_back = True

    db = FakeDB()
    image_bytes = BytesIO()
    PILImage.new("RGB", (100, 100), "blue").save(image_bytes, format="PNG")
    image_bytes.seek(0)
    upload = UploadFile(
        filename="test.png", file=image_bytes,
        headers={"content-type": "image/png"},
    )

    def fail_unlink(_path, *args, **kwargs):
        raise PermissionError("do not log the private path")

    def fail_create_image(*args, **kwargs):
        raise RuntimeError("Simulated database failure")

    monkeypatch.setattr(Path, "unlink", fail_unlink)
    monkeypatch.setattr("app.services.image_service.UPLOAD_DIR", tmp_path)
    monkeypatch.setattr("app.services.image_service.create_image", fail_create_image)

    with pytest.raises(RuntimeError, match="Simulated database failure"):
        upload_case_image(db, case_id, owner_id, upload)

    assert db.rolled_back is True
    assert caplog.records[-1].getMessage().startswith("Upload compensation failed")
    assert "do not log the private path" not in caplog.text
    assert len(list(tmp_path.rglob("*.png"))) == 1
    assert len(inspect_upload_storage([], tmp_path)["orphan_files"]) == 1
