from uuid import UUID

from sqlalchemy.orm import Session

from app.models.audit_log import AuditLog


def record_audit_event(
    db: Session,
    action: str,
    outcome: str,
    actor_user_id: UUID | None = None,
    resource_type: str | None = None,
    resource_id: str | None = None,
    client_ip: str | None = None,
) -> None:
    """Persist an audit event without secrets or free-form request data."""
    db.add(AuditLog(
        actor_user_id=actor_user_id,
        action=action,
        outcome=outcome,
        resource_type=resource_type,
        resource_id=resource_id,
        client_ip=client_ip,
    ))
    db.commit()
