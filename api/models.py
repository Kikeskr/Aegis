from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from api.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    wallet: Mapped["PaperWallet"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )


class PaperWallet(Base):
    __tablename__ = "paper_wallets"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )

    initial_balance: Mapped[float] = mapped_column(
        Float,
        default=10_000.0,
        nullable=False,
    )

    balance: Mapped[float] = mapped_column(
        Float,
        default=10_000.0,
        nullable=False,
    )

    realized_pnl: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    user: Mapped[User] = relationship(
        back_populates="wallet",
    )

    positions: Mapped[list["Position"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    trades: Mapped[list["Trade"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    equity_snapshots: Mapped[list["EquitySnapshot"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )

    event_records: Mapped[list["EventRecord"]] = relationship(
        back_populates="wallet",
        cascade="all, delete-orphan",
    )


class Position(Base):
    __tablename__ = "positions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("paper_wallets.id"),
        nullable=False,
    )

    asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    side: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    entry_price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    stop_loss: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    take_profit: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    wallet: Mapped[PaperWallet] = relationship(
        back_populates="positions",
    )


class Trade(Base):
    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("paper_wallets.id"),
        nullable=False,
    )

    asset: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    action: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    side: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    quantity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    price: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    pnl: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    return_pct: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    reasoning: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    confidence: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    wallet: Mapped[PaperWallet] = relationship(
        back_populates="trades",
    )


class EquitySnapshot(Base):
    __tablename__ = "equity_snapshots"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("paper_wallets.id"),
        nullable=False,
    )

    equity: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    wallet: Mapped[PaperWallet] = relationship(
        back_populates="equity_snapshots",
    )


class EventRecord(Base):
    """
    Permanent record of an event processed by Aegis.

    The JSON fields preserve the complete intelligence
    pipeline so the dashboard can reconstruct what Aegis
    saw, decided, approved/rejected, and executed.
    """

    __tablename__ = "event_records"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    wallet_id: Mapped[int] = mapped_column(
        ForeignKey("paper_wallets.id"),
        nullable=False,
    )

    event_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    sentiment: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    impact: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )

    affected_assets: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    filter_approved: Mapped[bool] = mapped_column(
        nullable=False,
    )

    filter_reason: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    decision_json: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    risk_json: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    execution_json: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    portfolio_json: Mapped[str] = mapped_column(
        Text,
        default="",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    wallet: Mapped[PaperWallet] = relationship(
        back_populates="event_records",
    )