import os
import time
from datetime import datetime, timedelta
from typing import Annotated, Dict, Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 14

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window = window_seconds
        self.requests: Dict[str, list[float]] = {}

    def check(self, key: str):
        now = time.time()
        history = self.requests.setdefault(key, [])
        cutoff = now - self.window
        while history and history[0] < cutoff:
            history.pop(0)
        if len(history) >= self.limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded, please try again later.",
            )
        history.append(now)


rate_limiter = RateLimiter(limit=20, window_seconds=60)
password_reset_tokens: Dict[str, tuple[str, float]] = {}
verification_tokens: Dict[str, tuple[str, float]] = {}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(user_id: int):
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"sub": str(user_id), "type": "refresh", "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> User:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        ) from err

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


def enforce_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "anonymous"
    rate_limiter.check(client_ip)


def create_email_token(
    email: str, store: Dict[str, tuple[str, float]], ttl_seconds: int = 3600
) -> str:
    token = create_access_token(
        {"sub": email, "purpose": "email"}, timedelta(seconds=ttl_seconds)
    )
    store[token] = (email, time.time() + ttl_seconds)
    return token


def consume_email_token(token: str, store: Dict[str, tuple[str, float]]) -> str:
    record = store.get(token)
    if not record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired token",
        )
    email, expires_at = record
    if time.time() > expires_at:
        store.pop(token, None)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token expired")
    store.pop(token, None)
    return email
