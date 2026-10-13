from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi import UploadFile
from io import BytesIO

from app.models.case import Case
from app.services.image_service import upload_case_image


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

    # Create a tiny valid PNG in memory
    from PIL import Image as PILImage

    image_bytes = BytesIO()
    PILImage.new("RGB", (2, 2), "red").save(image_bytes, format="PNG")
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