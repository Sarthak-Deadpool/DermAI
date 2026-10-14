import secrets

from itsdangerous import BadSignature, URLSafeTimedSerializer

from app.core.config import settings


CSRF_TOKEN_MAX_AGE_SECONDS = 30*60


def _get_serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(
        secret_key=settings.JWT_SECRET_KEY,
        salt="dermai-csrf-v1"
    )

def create_csrf_token() -> str:
    random_value = secrets.token_urlsafe(32)
    return _get_serializer().dumps(random_value)


def validate_csrf_token(token: str) -> bool:
    try:
        value = _get_serializer().loads(
            token,
            max_age=CSRF_TOKEN_MAX_AGE_SECONDS,
        )
        return isinstance(value, str) and bool(value)
    except (BadSignature, ValueError, TypeError):
        return False
