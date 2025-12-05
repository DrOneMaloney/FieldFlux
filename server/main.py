from datetime import timedelta
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from . import auth
from .auth import (
    consume_email_token,
    create_access_token,
    create_email_token,
    create_refresh_token,
    enforce_rate_limit,
    get_current_user,
    get_password_hash,
    password_reset_tokens,
    rate_limiter,
    verification_tokens,
    verify_password,
)
from .database import Base, engine, get_db
from .models import User
from .schemas import (
    EmailRequest,
    PasswordResetConfirm,
    TokenPayload,
    TokenResponse,
    UserCreate,
    UserLogin,
    UserResponse,
)

app = FastAPI(title="FieldFlux Auth API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.post("/signup", response_model=UserResponse)
def signup(
    payload: UserCreate, request: Request, db: Annotated[Session, Depends(get_db)]
):
    enforce_rate_limit(request)

    existing = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    hashed_password = get_password_hash(payload.password)
    user = User(email=payload.email.lower(), password_hash=hashed_password)
    db.add(user)
    db.commit()
    db.refresh(user)

    verification_token = create_email_token(user.email, verification_tokens)
    app.logger.info("Email verification token generated for %s: %s", user.email, verification_token)

    return user


@app.post("/login", response_model=TokenResponse)
def login(
    payload: UserLogin, request: Request, db: Annotated[Session, Depends(get_db)]
):
    enforce_rate_limit(request)

    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    access_token = create_access_token(
        {"sub": str(user.id)},
        expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_refresh_token(user.id)
    user.refresh_token = refresh_token
    db.commit()
    return TokenResponse(access_token=access_token, refresh_token=refresh_token)


@app.post("/logout")
def logout(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    current_user.refresh_token = None
    db.commit()
    return {"message": "Logged out"}


@app.post("/token/refresh", response_model=TokenResponse)
def refresh(token: str, db: Annotated[Session, Depends(get_db)]):
    try:
        payload = auth.jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid token type",
            )
        user_id = int(payload.get("sub"))
    except auth.JWTError as err:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        ) from err

    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.refresh_token != token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked",
        )

    new_access = create_access_token({"sub": str(user.id)})
    new_refresh = create_refresh_token(user.id)
    user.refresh_token = new_refresh
    db.commit()
    return TokenResponse(access_token=new_access, refresh_token=new_refresh)


@app.post("/password-reset/request")
def request_password_reset(
    payload: EmailRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    enforce_rate_limit(request)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        # Avoid leaking user existence
        return {"message": "If the account exists, reset instructions have been sent"}

    token = create_email_token(user.email, password_reset_tokens)
    app.logger.info("Password reset token for %s: %s", user.email, token)
    return {"message": "If the account exists, reset instructions have been sent"}


@app.post("/password-reset/confirm")
def reset_password(payload: PasswordResetConfirm, db: Annotated[Session, Depends(get_db)]):
    email = consume_email_token(payload.token, password_reset_tokens)
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.password_hash = get_password_hash(payload.new_password)
    user.refresh_token = None
    db.commit()
    return {"message": "Password updated"}


@app.post("/verify-email/request")
def request_verification(
    payload: EmailRequest, request: Request, db: Annotated[Session, Depends(get_db)]
):
    enforce_rate_limit(request)
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user:
        return {"message": "If the account exists, verification instructions have been sent"}

    token = create_email_token(user.email, verification_tokens)
    app.logger.info("Verification token for %s: %s", user.email, token)
    return {"message": "Verification email triggered"}


@app.post("/verify-email/confirm")
def confirm_email(payload: TokenPayload, db: Annotated[Session, Depends(get_db)]):
    email = consume_email_token(payload.token, verification_tokens)
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_verified = True
    db.commit()
    return {"message": "Email verified"}


@app.get("/me", response_model=UserResponse)
def me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rate_limit_remaining": {k: len(v) for k, v in rate_limiter.requests.items()},
    }
