"""Path validation for files stored under DermAI's private upload directory."""

from pathlib import Path

from fastapi import HTTPException, status


def resolve_upload_path(path: str | Path, storage_root: str | Path) -> Path:
    """Resolve a stored path and reject traversal or symlink escapes.

    Symlinks in the root-relative path are rejected, even when they currently
    resolve inside the root. This keeps authorization tied to the intended
    stored object and avoids a later symlink retarget changing that object.
    """
    root = Path(storage_root).resolve()
    candidate = Path(path)
    if not candidate.is_absolute():
        candidate = root / candidate

    try:
        lexical = Path(candidate)
        relative = lexical.relative_to(root)
    except ValueError:
        # A path with `..` may be lexically beneath root but resolve outside it;
        # check its resolved location below as well.
        relative = None

    if relative is None:
        try:
            resolved = candidate.resolve(strict=False)
            resolved.relative_to(root)
        except (OSError, ValueError):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            ) from None
        relative = resolved.relative_to(root)

    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        try:
            if cursor.is_symlink():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Image not found",
                )
        except OSError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Image not found",
            ) from None

    try:
        resolved = candidate.resolve(strict=False)
        resolved.relative_to(root)
    except (OSError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found",
        ) from None
    return resolved
