import secrets
import hmac

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import settings


CSRF_TOKEN_MAX_AGE_SECONDS = 30*60


def _get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.CSRF_SECRET_KEY,
        salt="dermai-csrf-v1"
    )

def create_csrf_token() -> str:
    random_value = secrets.token_urlsafe(32)
    return _get_serializer().dumps(random_value)


def validate_csrf_token(submitted_token : str,
                        csrf_cookie_token: str) -> bool:
    
    if not submitted_token or not csrf_cookie_token:
        return False
    
    
    if not hmac.compare_digest(
        submitted_token,
        csrf_cookie_token,
    ):
        return False
    
    try:
        value = _get_serializer().loads(
            submitted_token,
            max_age=CSRF_TOKEN_MAX_AGE_SECONDS,
        )
        
    except(BadSignature, ValueError, TypeError):
        return False
    
    return isinstance(value, str) and bool(value);
   
