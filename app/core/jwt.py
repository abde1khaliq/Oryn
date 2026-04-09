import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone
from app.core.config import settings

def create_access_token(user_id: str, tenant_id: str) -> str:
    payload = {
        'user_id': str(user_id),
        'tenant_id': str(tenant_id),
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def decode_access_token(access_token: str) -> dict:
    try:
        return jwt.decode(access_token, settings.secret_key, algorithms=[settings.algorithm])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail='Token has expired.')
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail='Invalid token.')