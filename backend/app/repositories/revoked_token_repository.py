from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.revoked_token import RevokedToken


def revoke_token(
    db: Session,
    jti: str,
    expires_at: datetime,
) -> RevokedToken:
    revoke_token = RevokedToken(
        jti =jti,
        expires_at = expires_at,
    )
    
    db.add(revoke_token)
    db.commit()
    db.refresh(revoke_token)
    
    return revoke_token

def is_token_revoked(db: Session, jti: str) -> bool:
    statement = select(RevokedToken.jti).where(
        RevokedToken.jti == jti
    )
    
    return db.scalar(statement) is not None

def delete_expired_revoked_token(db: Session) -> int:
    now = datetime.now(timezone.utc)
    
    statement = select(RevokedToken).where(
        RevokedToken.expires_at <= now
    )
    
    expired_token = db.scalar(statement).all()
    
    for token in expired_token:
        db.delete(token)
    db.commit()
    
    return len(expired_token)