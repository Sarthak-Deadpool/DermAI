from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.dependencies.auth import get_current_user
from app.models.user import User, UserRole
from app.dependencies.database import get_db
from app.services.audit_service import record_audit_event


def require_roles(*allowed_roles: UserRole):
    def role_checker(
        request: Request,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user),
        
    ) -> User:
        if current_user.role not in allowed_roles:
            record_audit_event(db, "access_denied", "failure", current_user.id, client_ip=request.client.host if request and request.client else None)
            raise HTTPException(
                  status_code=status.HTTP_403_FORBIDDEN,
                  detail="You do not have permission to access this resource",
            )
            
        return current_user
    
    return role_checker
