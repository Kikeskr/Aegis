from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: EmailStr

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class PortfolioResponse(BaseModel):
    user_id: int
    username: str
    initial_balance: float
    cash_balance: float
    realized_pnl: float
    unrealized_pnl: float
    total_equity: float
    return_pct: float


class PositionResponse(BaseModel):
    id: int
    asset: str
    side: str
    quantity: float
    entry_price: float
    current_price: float
    stop_loss: float
    take_profit: float
    unrealized_pnl: float
    return_pct: float


class TradeResponse(BaseModel):
    id: int
    asset: str
    action: str
    side: str
    quantity: float
    price: float
    pnl: float
    return_pct: float
    status: str
    reasoning: str
    confidence: float
    created_at: datetime

    class Config:
        from_attributes = True


class EquityResponse(BaseModel):
    equity: float
    created_at: datetime

    class Config:
        from_attributes = True


class EventRecordResponse(BaseModel):
    id: int
    event_type: str
    description: str
    sentiment: str
    impact: str
    affected_assets: list[str]

    filter_approved: bool
    filter_reason: str

    decision: dict | None
    risk: dict | None
    execution: dict | None
    portfolio: dict | None

    created_at: datetime