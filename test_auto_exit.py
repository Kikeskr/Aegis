from api.database import SessionLocal
from api import models
from agent.price_feed import PriceFeed
from api.aegis_service import AegisService


db = SessionLocal()

try:
    # ============================================================
    # GET TEST USER
    # ============================================================

    user = (
        db.query(models.User)
        .filter(
            models.User.username == "testuser"
        )
        .first()
    )

    if not user:
        raise RuntimeError(
            "testuser was not found."
        )

    wallet = (
        db.query(models.PaperWallet)
        .filter(
            models.PaperWallet.user_id == user.id
        )
        .first()
    )

    if not wallet:
        raise RuntimeError(
            "testuser wallet was not found."
        )

    service = AegisService(
        db=db,
        wallet=wallet,
    )

    positions = service.get_positions()

    if not positions:
        raise RuntimeError(
            "testuser has no open positions."
        )

    # ============================================================
    # SELECT FIRST LONG POSITION
    # ============================================================

    asset = next(iter(positions))
    position = positions[asset]

    if position["side"] != "LONG":
        raise RuntimeError(
            "This test expects a LONG position."
        )

    price_feed = PriceFeed()

    current_price = price_feed.get_price(
        asset
    )

    # ============================================================
    # FIND DATABASE POSITION
    # ============================================================

    position_row = (
        db.query(models.Position)
        .filter(
            models.Position.wallet_id == wallet.id,
            models.Position.asset == asset,
        )
        .first()
    )

    if not position_row:
        raise RuntimeError(
            f"Database position for {asset} "
            "was not found."
        )

    original_take_profit = (
        position_row.take_profit
    )

    original_stop_loss = (
        position_row.stop_loss
    )

    # ============================================================
    # FORCE TAKE-PROFIT CONDITION
    # ============================================================
    #
    # Aegis stores stop-loss / take-profit as decimal
    # percentages.
    #
    # 0.09 = 9%
    # 0.04 = 4%
    #
    # Setting take_profit to 0.0 means:
    #
    # current price >= entry price
    #
    # which is already true for this test position.
    # ============================================================

    position_row.take_profit = 0.0

    db.commit()

    print("=" * 70)
    print("AEGIS CONTROLLED AUTO-EXIT TEST")
    print("=" * 70)

    print(
        f"User: {user.username}"
    )

    print(
        f"Asset: {asset}"
    )

    print(
        f"Side: {position['side']}"
    )

    print(
        f"Entry: ${position['entry_price']:.2f}"
    )

    print(
        f"Current price: ${current_price:.2f}"
    )

    print(
        f"Original stop-loss: "
        f"{original_stop_loss * 100:.2f}%"
    )

    print(
        f"Original take-profit: "
        f"{original_take_profit * 100:.2f}%"
    )

    print(
        "Temporary take-profit: 0.00%"
    )

    print()
    print(
        "Running Aegis position monitor..."
    )
    print()

    # ============================================================
    # RUN AUTO-EXIT
    # ============================================================

    result = service.monitor_positions()

    for item in result:
        print(item)

    db.commit()

    print()
    print("=" * 70)
    print("AUTO-EXIT TEST COMPLETE")
    print("=" * 70)

finally:
    db.close()