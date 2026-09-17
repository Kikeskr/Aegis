from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

from api import models
from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from api.database import Base, engine, get_db
from api.schemas import (
    LoginRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)


# ---------------------------------------------------------
# DATABASE
# ---------------------------------------------------------

Base.metadata.create_all(
    bind=engine,
)


# ---------------------------------------------------------
# FASTAPI
# ---------------------------------------------------------

app = FastAPI(
    title="Aegis API",
    description="Autonomous event-driven AI trading agent",
    version="1.0.0",
)


# ---------------------------------------------------------
# ROOT
# ---------------------------------------------------------

@app.get("/")
def root():
    return {
        "name": "Aegis",
        "status": "online",
    }


# ---------------------------------------------------------
# HEALTH
# ---------------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "healthy",
    }


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.post(
    "/auth/register",
    response_model=UserResponse,
)
def register(
    user: UserCreate,
    db: Session = Depends(get_db),
):
    existing_username = (
        db.query(models.User)
        .filter(
            models.User.username
            == user.username
        )
        .first()
    )

    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="Username already exists.",
        )

    existing_email = (
        db.query(models.User)
        .filter(
            models.User.email
            == user.email
        )
        .first()
    )

    if existing_email:
        raise HTTPException(
            status_code=400,
            detail="Email already exists.",
        )

    new_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hash_password(
            user.password
        ),
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    wallet = models.PaperWallet(
        user_id=new_user.id,
        balance=10_000.0,
        realized_pnl=0.0,
    )

    db.add(wallet)
    db.commit()

    return new_user


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.post(
    "/auth/login",
    response_model=TokenResponse,
)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db),
):
    user = (
        db.query(models.User)
        .filter(
            models.User.email
            == credentials.email
        )
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(
        credentials.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_access_token(
        user_id=user.id,
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# ---------------------------------------------------------
# CURRENT USER
# ---------------------------------------------------------

@app.get(
    "/auth/me",
    response_model=UserResponse,
)
def get_me(
    current_user: models.User = Depends(
        get_current_user
    ),
):
    return current_user


# ---------------------------------------------------------
# AUTHENTICATED WALLET
# ---------------------------------------------------------

@app.get("/wallet")
def get_my_wallet(
    current_user: models.User = Depends(
        get_current_user
    ),
    db: Session = Depends(get_db),
):
    wallet = (
        db.query(models.PaperWallet)
        .filter(
            models.PaperWallet.user_id
            == current_user.id
        )
        .first()
    )

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found.",
        )

    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "balance": wallet.balance,
        "realized_pnl": wallet.realized_pnl,
    }


# ---------------------------------------------------------
# TEMPORARY WALLET TEST
# ---------------------------------------------------------

@app.get("/wallet/{user_id}")
def get_wallet_by_id(
    user_id: int,
    db: Session = Depends(get_db),
):
    wallet = (
        db.query(models.PaperWallet)
        .filter(
            models.PaperWallet.user_id
            == user_id
        )
        .first()
    )

    if not wallet:
        raise HTTPException(
            status_code=404,
            detail="Wallet not found.",
        )

    return {
        "user_id": user_id,
        "balance": wallet.balance,
        "realized_pnl": wallet.realized_pnl,
    }