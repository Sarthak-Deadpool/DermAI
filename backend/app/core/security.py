from datetime import datetime, timedelta, timezone

import jwt
import uuid
from pwdlib import PasswordHash

from app.core.config import settings


password_hash = PasswordHash.recommended()

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
TOKEN_TYPE = "access"

def hash_password(password: str) -> str:
    #Hashed password before storing it in database
    return password_hash.hash(password)

def verify_password(password: str, hashed_password: str) -> bool:
    #Verify Password against its Hashed
    return password_hash.verify(password, hashed_password);


def create_access_token(subject:str) ->str:
    #create sort time access token
    if not subject or not subject.strip():
        raise ValueError("Token subject must not be empty")
    
    now = datetime.now(timezone.utc)
    expires_at = now +timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )
    payload = {
        "sub" :subject,
        "jti": uuid.uuid4().hex,
        "iat":now,
        "exp":expires_at,
        "type" : TOKEN_TYPE,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=ALGORITHM,
    )

def decode_access_token(token: str) -> dict:
    # decode and validate an access token 
    
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[ALGORITHM],
        options={
             "require": ["sub", "jti", "iat", "exp", "type"],
        }
    )
    
    if payload.get("type") != TOKEN_TYPE:
        raise jwt.InvalidTokenError("Invalid token type")
    
    subject = payload.get("sub")
    
    if not isinstance(subject, str) or not subject.strip():
        raise jwt.InvalidTokenError("Invalid token subject")
    
    return payload