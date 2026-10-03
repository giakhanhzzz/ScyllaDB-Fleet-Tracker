import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from app.config import settings
from app.database import db

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return "$".join(("scrypt", "16384", "8", "1", salt.hex(), digest.hex()))

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        method, n, r, p, salt, expected = hashed_password.split("$")
        if (method, n, r, p) != ("scrypt", "16384", "8", "1"):
            return False
        digest = hashlib.scrypt(plain_password.encode(), salt=bytes.fromhex(salt), n=16384, r=8, p=1)
        return hmac.compare_digest(digest.hex(), expected)
    except (ValueError, TypeError):
        return False

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if not payload.get("sub") or not payload.get("exp"):
            raise JWTError("Missing subject or expiry")
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token xác thực không hợp lệ hoặc đã hết hạn"
        )

def current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_token(token)
    row = db.execute(db.prepared_statements["login"], (payload["sub"],)).one()
    if not row or not row.active:
        raise HTTPException(401, "Tài khoản không tồn tại hoặc đã bị khóa")
    return {"sub": row.username, "username": row.username, "full_name": row.full_name,
            "role": row.role, "company_id": row.company_id}

def require_role(allowed_roles: list[str]):
    def role_checker(user: dict = Depends(current_user)):
        user_role = user["role"]
        if user_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Quyền truy cập bị từ chối. Yêu cầu một trong các quyền: {', '.join(allowed_roles)}"
            )
        return user
    return role_checker
