from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


def revoke_token(
    db: Session,
    jti: str,
    expires_at: datetime,
) -> RevokedToken:
    revoked = RevokedToken(
        jti =jti,
        expires_at = expires_at,
    )
    try:
        db.add(revoked)
        db.commit()
        db.refresh(revoked)
        return revoked
    except Exception:
        db.rollback()
        raise
    

def is_token_revoked(db: Session, jti: str) -> bool:
    statement = select(RevokedToken.jti).where(
        RevokedToken.jti == jti
    )
    
    return db.scalar(statement) is not None

def delete_expired_revoked_token(db: Session) -> int:
    now = datetime.now(timezone.utc)
    
    statement = delete(RevokedToken).where(
        RevokedToken.expires_at <= now
    )
    
    
    try:
        result = db.execute(statement)
        deleted_count = result.rowcount or 0
        db.commit()
        return deleted_count
    except Exception:
        db.rollback()
        raise
