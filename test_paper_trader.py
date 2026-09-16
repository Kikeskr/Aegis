from agent.schemas import TradeDecision
from execution.paper_trader import PaperTrader


# ========================================
# START WITH A CLEAN PORTFOLIO
# ========================================

trader = PaperTrader(
    starting_balance=10_000
)

trader.reset()

print("\n" + "=" * 60)
print("PAPER TRADER TEST")
print("=" * 60)

print("\nStarting Balance:")
print(f"${trader.balance:.2f}")


# ========================================
# TEST 1: LONG + TAKE PROFIT
# ========================================

print("\n" + "=" * 60)
print("TEST 1: LONG POSITION + TAKE PROFIT")
print("=" * 60)


buy_decision = TradeDecision(
    asset="AAPL",
    action="BUY",
    confidence=0.85,
    position_size=0.10,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Testing long position take-profit.",
)


result = trader.execute(
    decision=buy_decision,
    price=100.00,
)


print("\nOPEN LONG")
print(result)


current_price = 111.00

print("\nCURRENT PRICE")
print(f"AAPL: ${current_price:.2f}")


exit_result = trader.check_exit(
    asset="AAPL",
    current_price=current_price,
)


print("\nPOSITION MONITOR")
print(exit_result)


# ========================================
# TEST 2: SHORT + TAKE PROFIT
# ========================================

print("\n" + "=" * 60)
print("TEST 2: SHORT POSITION + TAKE PROFIT")
print("=" * 60)


short_decision = TradeDecision(
    asset="GOOGL",
    action="SELL",
    confidence=0.80,
    position_size=0.10,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Testing short position take-profit.",
)


result = trader.execute(
    decision=short_decision,
    price=200.00,
)


print("\nOPEN SHORT")
print(result)


current_price = 175.00

print("\nCURRENT PRICE")
print(f"GOOGL: ${current_price:.2f}")


exit_result = trader.check_exit(
    asset="GOOGL",
    current_price=current_price,
)


print("\nPOSITION MONITOR")
print(exit_result)


# ========================================
# TEST 3: SHORT + STOP LOSS
# ========================================

print("\n" + "=" * 60)
print("TEST 3: SHORT POSITION + STOP LOSS")
print("=" * 60)


short_stop_decision = TradeDecision(
    asset="TSLA",
    action="SELL",
    confidence=0.85,
    position_size=0.10,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Testing short position stop-loss.",
)


result = trader.execute(
    decision=short_stop_decision,
    price=200.00,
)


print("\nOPEN SHORT")
print(result)


current_price = 215.00

print("\nCURRENT PRICE")
print(f"TSLA: ${current_price:.2f}")


exit_result = trader.check_exit(
    asset="TSLA",
    current_price=current_price,
)


print("\nPOSITION MONITOR")
print(exit_result)


# ========================================
# FINAL ACCOUNT STATE
# ========================================

print("\n" + "=" * 60)
print("FINAL ACCOUNT STATE")
print("=" * 60)


print("\nFINAL BALANCE")
print(f"${trader.balance:.2f}")


print("\nREALIZED P&L")
print(f"${trader.realized_pnl:.2f}")


print("\nOPEN POSITIONS")
print(trader.positions)


print("\nTRADE HISTORY")

for trade in trader.trade_history:
    print(trade)


print("\nEQUITY CURVE")
print(trader.equity_curve)


print("\n" + "=" * 60)
print("PAPER TRADER TEST COMPLETE")
print("=" * 60)