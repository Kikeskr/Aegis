from agent.schemas import TradeDecision
from api.database import Base, SessionLocal, engine
from api.models import PaperWallet, Position, Trade, User
from execution.database_paper_trader import (
    DatabasePaperTrader,
)


def run_test():
    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    try:
        user = User(
            username="trader_test",
            email="trader_test@example.com",
            password_hash="test_hash",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        wallet = PaperWallet(
            user_id=user.id,
            balance=10_000.0,
            realized_pnl=0.0,
        )

        db.add(wallet)
        db.commit()
        db.refresh(wallet)

        trader = DatabasePaperTrader(
            db=db,
            wallet=wallet,
        )

        # ---------------------------------------------
        # TEST 1: BUY
        # ---------------------------------------------

        buy_decision = TradeDecision(
            asset="NVDA",
            action="BUY",
            confidence=0.90,
            position_size=0.10,
            stop_loss=0.05,
            take_profit=0.10,
            reasoning="Test BUY.",
        )

        result = trader.execute(
            decision=buy_decision,
            price=200.0,
        )

        print("\nTEST 1: BUY")
        print(result)

        db.refresh(wallet)

        print(
            f"Balance: ${wallet.balance:.2f}"
        )

        positions = trader.get_positions()

        print(
            "Positions:",
            positions,
        )

        assert len(positions) == 1
        assert "NVDA" in positions
        assert positions["NVDA"]["side"] == "LONG"

        # ---------------------------------------------
        # TEST 2: DUPLICATE BUY
        # ---------------------------------------------

        result = trader.execute(
            decision=buy_decision,
            price=205.0,
        )

        print("\nTEST 2: DUPLICATE BUY")
        print(result)

        assert "already exists" in result

        # ---------------------------------------------
        # TEST 3: SELL / EXIT
        # ---------------------------------------------

        sell_decision = TradeDecision(
            asset="NVDA",
            action="SELL",
            confidence=0.90,
            position_size=1.0,
            stop_loss=0.0,
            take_profit=0.0,
            reasoning="Test exit.",
        )

        result = trader.execute(
            decision=sell_decision,
            price=210.0,
        )

        print("\nTEST 3: SELL / EXIT")
        print(result)

        db.refresh(wallet)

        positions = trader.get_positions()

        print(
            "Positions:",
            positions,
        )

        print(
            f"Balance: ${wallet.balance:.2f}"
        )

        print(
            f"Realized P&L: "
            f"${wallet.realized_pnl:.2f}"
        )

        assert len(positions) == 0
        assert wallet.realized_pnl > 0

        # ---------------------------------------------
        # TEST 4: DATABASE TRADES
        # ---------------------------------------------

        trades = (
            db.query(Trade)
            .filter(
                Trade.wallet_id == wallet.id
            )
            .all()
        )

        print("\nTEST 4: TRADE HISTORY")
        print(
            f"Trades recorded: {len(trades)}"
        )

        assert len(trades) == 2

        print("\nDATABASE PAPER TRADER TEST PASSED.")

    finally:
        db.rollback()

        db.query(Trade).filter(
            Trade.wallet_id == wallet.id
        ).delete()

        db.query(Position).filter(
            Position.wallet_id == wallet.id
        ).delete()

        db.query(PaperWallet).filter(
            PaperWallet.id == wallet.id
        ).delete()

        db.query(User).filter(
            User.id == user.id
        ).delete()

        db.commit()
        db.close()


if __name__ == "__main__":
    run_test()