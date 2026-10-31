import secrets
import hmac
import hashlib
import base64

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


def create_session_csrf_token(session_id: str) -> str:
    """Derive a deterministic token bound to one opaque browser session."""
    if not session_id:
        raise ValueError("Session identifier must not be empty")
    message = b"dermai-session-csrf-v1:" + session_id.encode("utf-8")
    digest = hmac.new(settings.CSRF_SECRET_KEY.encode("utf-8"), message, hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")


def validate_session_csrf_token(submitted_token: str, session_id: str) -> bool:
    if not submitted_token or not session_id:
        return False
    expected = create_session_csrf_token(session_id)
    return hmac.compare_digest(submitted_token, expected)


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
   
