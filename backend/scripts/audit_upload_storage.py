"""Read-only upload storage reconciliation for an explicitly disposable test DB."""

import argparse
import json
from pathlib import Path

from sqlalchemy import create_engine, select
from sqlalchemy.engine import URL
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.image import Image
from app.services.image_cleanup import inspect_upload_storage
from app.services.image_service import UPLOAD_DIR


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--storage-root", type=Path, default=UPLOAD_DIR)
    parser.add_argument(
        "--confirm-disposable-test-db",
        action="store_true",
        help="required; confirms this read-only audit targets an isolated loopback *_test database",
    )
    args = parser.parse_args()

    if not args.confirm_disposable_test_db:
        parser.error("refusing database access without --confirm-disposable-test-db")
    if (
        settings.APP_ENV != "test"
        or settings.DB_HOST not in {"localhost", "127.0.0.1", "::1"}
        or not settings.DB_NAME.endswith("_test")
    ):
        parser.error("refusing non-test or non-loopback database configuration")

    url = URL.create(
        "postgresql+psycopg",
        username=settings.DB_USER,
        password=settings.DB_PASSWORD,
        host=settings.DB_HOST,
        port=settings.DB_PORT,
        database=settings.DB_NAME,
    )
    engine = create_engine(url, pool_pre_ping=True)
    try:
        with Session(engine) as db:
            rows = db.scalars(select(Image)).all()
            print(json.dumps(inspect_upload_storage(rows, args.storage_root), indent=2))
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
