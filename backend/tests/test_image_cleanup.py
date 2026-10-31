from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.services.image_cleanup import cleanup_uploaded_file, inspect_upload_storage


def test_cleanup_retries_transient_unlink_failure(tmp_path, monkeypatch):
    target = tmp_path / "case" / "random.png"
    target.parent.mkdir()
    target.write_bytes(b"synthetic")
    original_unlink = Path.unlink
    calls = 0

    def fail_once(path, *args, **kwargs):
        nonlocal calls
        calls += 1
        if calls == 1:
            raise PermissionError("transient")
        return original_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_once)
    assert cleanup_uploaded_file(target, retry_delay_seconds=0) is True
    assert calls == 2
    assert not target.exists()


def test_persistent_cleanup_failure_logs_safe_context_and_is_reconcilable(
    tmp_path, monkeypatch, caplog
):
    target = tmp_path / "case" / "random-upload.png"
    target.parent.mkdir()
    target.write_bytes(b"synthetic image")

    def fail_always(_path, *args, **kwargs):
        raise PermissionError("private path should not be logged")

    monkeypatch.setattr(Path, "unlink", fail_always)
    assert cleanup_uploaded_file(target, attempts=2, retry_delay_seconds=0) is False
    assert caplog.records[0].storage_filename == "random-upload.png"
    assert str(tmp_path) not in caplog.text
    assert "private path should not be logged" not in caplog.text

    audit = inspect_upload_storage([], tmp_path)
    assert audit["orphan_files"] == ["case/random-upload.png"]


def test_reconciliation_detects_missing_unsafe_and_orphaned_files(tmp_path):
    root = tmp_path / "private"
    case_dir = root / "case"
    case_dir.mkdir(parents=True)
    existing = case_dir / "existing.png"
    existing.write_bytes(b"present")
    orphan = case_dir / "orphan.jpg"
    orphan.write_bytes(b"unreferenced")
    missing_id = uuid4()
    unsafe_id = uuid4()
    existing_id = uuid4()
    rows = [
        SimpleNamespace(id=existing_id, file_path=str(existing)),
        SimpleNamespace(id=missing_id, file_path=str(case_dir / "missing.png")),
        SimpleNamespace(id=unsafe_id, file_path=str(tmp_path / "outside.png")),
    ]

    report = inspect_upload_storage(rows, root)

    assert report["database_image_rows"] == 3
    assert report["missing_file_image_ids"] == [str(missing_id)]
    assert report["unsafe_path_image_ids"] == [str(unsafe_id)]
    assert report["orphan_files"] == ["case/orphan.jpg"]
