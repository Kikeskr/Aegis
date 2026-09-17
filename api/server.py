from contextlib import asynccontextmanager
from pathlib import Path
import json

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from agent.background_worker import AegisBackgroundWorker
from agent.events import MarketEvent
from agent.price_feed import PriceFeed

from api import models
from api.aegis_service import AegisService

from api.auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)

from api.database import (
    Base,
    engine,
    get_db,
)

from api.schemas import (
    EquityResponse,
    EventRecordResponse,
    LoginRequest,
    PortfolioResponse,
    PositionResponse,
    TokenResponse,
    TradeResponse,
    UserCreate,
    UserResponse,
)

from execution.database_paper_trader import (
    DatabasePaperTrader,
)


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(
    __file__
).resolve().parent.parent

FRONTEND_DIR = BASE_DIR / "frontend"


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(
    bind=engine
)


# ============================================================
# BACKGROUND WORKER
# ============================================================

aegis_worker = AegisBackgroundWorker(
    interval=60
)


@asynccontextmanager
async def lifespan(app: FastAPI):

    print(
        "[AEGIS] Starting autonomous event engine..."
    )

    aegis_worker.start()

    print(
        "[AEGIS] Autonomous event engine online."
    )

    yield

    print(
        "[AEGIS] Stopping autonomous event engine..."
    )

    aegis_worker.stop()

    print(
        "[AEGIS] Autonomous event engine stopped."
    )


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="Aegis API",
    description=(
        "Autonomous event-driven AI trading agent"
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ============================================================
# FRONTEND
# ============================================================

app.mount(
    "/static",
    StaticFiles(
        directory=FRONTEND_DIR
    ),
    name="static",
)


@app.get("/")
def frontend():

    return FileResponse(
        FRONTEND_DIR / "index.html"
    )


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "worker_running": aegis_worker.running,
    }


# ============================================================
# REGISTER
# ============================================================

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
        initial_balance=10_000.0,
        balance=10_000.0,
        realized_pnl=0.0,
    )

    db.add(wallet)
    db.commit()

    return new_user


# ============================================================
# LOGIN
# ============================================================

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
        user_id=user.id
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }


# ============================================================
# CURRENT USER
# ============================================================

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


# ============================================================
# PORTFOLIO
# ============================================================

@app.get(
    "/portfolio",
    response_model=PortfolioResponse,
)
def get_portfolio(
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
            detail="Portfolio not found.",
        )

    trader = DatabasePaperTrader(
        db=db,
        wallet=wallet,
    )

    positions = trader.get_positions()

    price_feed = PriceFeed()

    current_prices = {}
    unrealized_pnl = 0.0

    for asset, position in positions.items():

        try:

            current_price = (
                price_feed.get_price(
                    asset
                )
            )

        except Exception:

            current_price = (
                position["entry_price"]
            )

        current_prices[asset] = (
            current_price
        )

        quantity = position[
            "quantity"
        ]

        entry_price = position[
            "entry_price"
        ]

        side = position[
            "side"
        ]

        if side == "LONG":

            position_pnl = (
                current_price
                - entry_price
            ) * quantity

        else:

            position_pnl = (
                entry_price
                - current_price
            ) * quantity

        unrealized_pnl += position_pnl

    total_equity = (
        trader.calculate_equity(
            current_prices=current_prices
        )
    )

    return_pct = (
        trader.calculate_portfolio_return(
            equity=total_equity
        )
    )

    return {

        "user_id":
            current_user.id,

        "username":
            current_user.username,

        "initial_balance":
            wallet.initial_balance,

        "cash_balance":
            wallet.balance,

        "realized_pnl":
            wallet.realized_pnl,

        "unrealized_pnl":
            unrealized_pnl,

        "total_equity":
            total_equity,

        "return_pct":
            return_pct,
    }


# ============================================================
# POSITIONS
# ============================================================

@app.get(
    "/positions",
    response_model=list[
        PositionResponse
    ],
)
def get_positions(
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
            detail="Portfolio not found.",
        )

    trader = DatabasePaperTrader(
        db=db,
        wallet=wallet,
    )

    positions = trader.get_positions()

    price_feed = PriceFeed()

    response = []

    for asset, position in positions.items():

        try:

            current_price = (
                price_feed.get_price(
                    asset
                )
            )

        except Exception:

            current_price = (
                position["entry_price"]
            )

        quantity = position[
            "quantity"
        ]

        entry_price = position[
            "entry_price"
        ]

        side = position[
            "side"
        ]

        if side == "LONG":

            unrealized_pnl = (
                current_price
                - entry_price
            ) * quantity

        else:

            unrealized_pnl = (
                entry_price
                - current_price
            ) * quantity

        if entry_price != 0:

            if side == "LONG":

                position_return = (
                    (
                        current_price
                        - entry_price
                    )
                    / entry_price
                ) * 100

            else:

                position_return = (
                    (
                        entry_price
                        - current_price
                    )
                    / entry_price
                ) * 100

        else:

            position_return = 0.0

        db_position = (
            db.query(models.Position)
            .filter(
                models.Position.wallet_id
                == wallet.id,
                models.Position.asset
                == asset,
            )
            .first()
        )

        response.append({

            "id":
                db_position.id
                if db_position
                else 0,

            "asset":
                asset,

            "side":
                side,

            "quantity":
                quantity,

            "entry_price":
                entry_price,

            "current_price":
                current_price,

            "stop_loss":
                position[
                    "stop_loss"
                ],

            "take_profit":
                position[
                    "take_profit"
                ],

            "unrealized_pnl":
                unrealized_pnl,

            "return_pct":
                position_return,
        })

    return response


# ============================================================
# MANUAL POSITION CLOSE
# ============================================================

@app.post(
    "/positions/{position_id}/close"
)
def close_position(
    position_id: int,
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
            detail="Portfolio not found.",
        )

    position = (
        db.query(models.Position)
        .filter(
            models.Position.id
            == position_id,
            models.Position.wallet_id
            == wallet.id,
        )
        .first()
    )

    if not position:

        raise HTTPException(
            status_code=404,
            detail="Position not found.",
        )

    price_feed = PriceFeed()

    try:

        current_price = (
            price_feed.get_price(
                position.asset
            )
        )

    except Exception as error:

        raise HTTPException(
            status_code=503,
            detail=(
                "Unable to retrieve current "
                f"price for {position.asset}."
            ),
        ) from error

    trader = DatabasePaperTrader(
        db=db,
        wallet=wallet,
    )

    message = trader.close_position(
        position=position,
        price=current_price,
    )

    return {
        "success": True,
        "message": message,
        "position_id": position_id,
        "asset": position.asset,
        "price": current_price,
    }


# ============================================================
# TRADES
# ============================================================

@app.get(
    "/trades",
    response_model=list[
        TradeResponse
    ],
)
def get_trades(
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
            detail="Portfolio not found.",
        )

    return (
        db.query(models.Trade)
        .filter(
            models.Trade.wallet_id
            == wallet.id
        )
        .order_by(
            models.Trade.created_at.desc()
        )
        .all()
    )


# ============================================================
# PERFORMANCE
# ============================================================

@app.get(
    "/performance",
    response_model=list[
        EquityResponse
    ],
)
def get_performance(
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
            detail="Portfolio not found.",
        )

    return (
        db.query(
            models.EquitySnapshot
        )
        .filter(
            models.EquitySnapshot.wallet_id
            == wallet.id
        )
        .order_by(
            models.EquitySnapshot.created_at.asc()
        )
        .all()
    )


# ============================================================
# MANUAL EVENT PROCESSING
# ============================================================

@app.post(
    "/agent/process-event"
)
def process_event(
    event: MarketEvent,
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
            detail="Portfolio not found.",
        )

    service = AegisService(
        db=db,
        wallet=wallet,
    )

    return service.process_event(
        event
    )


# ============================================================
# POSITION MONITORING
# ============================================================

@app.post(
    "/agent/monitor"
)
def monitor_positions(
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
            detail="Portfolio not found.",
        )

    service = AegisService(
        db=db,
        wallet=wallet,
    )

    results = (
        service.monitor_positions()
    )

    return {

        "user_id":
            current_user.id,

        "positions_checked":
            len(results),

        "results":
            results,
    }


# ============================================================
# EVENT HISTORY
# ============================================================

@app.get(
    "/events",
    response_model=list[
        EventRecordResponse
    ],
)
def get_events(
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
            detail="Portfolio not found.",
        )

    records = (
        db.query(
            models.EventRecord
        )
        .filter(
            models.EventRecord.wallet_id
            == wallet.id
        )
        .order_by(
            models.EventRecord.created_at.desc()
        )
        .all()
    )

    response = []

    for record in records:

        response.append({

            "id":
                record.id,

            "event_type":
                record.event_type,

            "description":
                record.description,

            "sentiment":
                record.sentiment,

            "impact":
                record.impact,

            "affected_assets":
                json.loads(
                    record.affected_assets
                ),

            "filter_approved":
                record.filter_approved,

            "filter_reason":
                record.filter_reason,

            "decision":
                (
                    json.loads(
                        record.decision_json
                    )
                    if record.decision_json
                    else None
                ),

            "risk":
                (
                    json.loads(
                        record.risk_json
                    )
                    if record.risk_json
                    else None
                ),

            "execution":
                (
                    json.loads(
                        record.execution_json
                    )
                    if record.execution_json
                    else None
                ),

            "portfolio":
                (
                    json.loads(
                        record.portfolio_json
                    )
                    if record.portfolio_json
                    else None
                ),

            "created_at":
                record.created_at,
        })

    return response


# ============================================================
# AUTONOMOUS ENGINE STATUS
# ============================================================

@app.get(
    "/agent/status"
)
def worker_status(
    current_user: models.User = Depends(
        get_current_user
    ),
):

    return aegis_worker.get_status()


# ============================================================
# DEBUG WALLET
# ============================================================

@app.get(
    "/wallet/{user_id}"
)
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

        "user_id":
            user_id,

        "initial_balance":
            wallet.initial_balance,

        "balance":
            wallet.balance,

        "realized_pnl":
            wallet.realized_pnl,
    }