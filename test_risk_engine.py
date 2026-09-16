from agent.schemas import TradeDecision
from risk.risk_engine import RiskEngine


risk_engine = RiskEngine()


print("=" * 60)
print("AEGIS RISK ENGINE TEST")
print("=" * 60)


# --------------------------------------------------
# EXISTING PORTFOLIO
# --------------------------------------------------

portfolio = {
    "NVDA": {
        "quantity": 2.82,
        "entry_price": 215.93,
        "stop_loss": 0.05,
        "take_profit": 0.12,
        "side": "LONG",
    }
}

print("\nCURRENT PORTFOLIO")
print("-" * 60)
print("NVDA:", portfolio["NVDA"])


# --------------------------------------------------
# TEST 1: NORMAL BUY
# --------------------------------------------------

print("\nTEST 1: NORMAL BUY")
print("-" * 60)

buy_decision = TradeDecision(
    asset="AAPL",
    action="BUY",
    confidence=0.80,
    position_size=0.05,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Strong positive market event.",
)

approved, reason = risk_engine.evaluate(
    decision=buy_decision,
    current_positions=portfolio,
)

print("Approved:", approved)
print("Reason:", reason)


# --------------------------------------------------
# TEST 2: FULL NVDA LONG EXIT
# --------------------------------------------------

print("\nTEST 2: FULL NVDA LONG EXIT")
print("-" * 60)

exit_decision = TradeDecision(
    asset="NVDA",
    action="SELL",
    confidence=0.90,
    position_size=1.0,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Negative event requires closing the existing NVDA LONG.",
)

approved, reason = risk_engine.evaluate(
    decision=exit_decision,
    current_positions=portfolio,
)

print("Approved:", approved)
print("Reason:", reason)


# --------------------------------------------------
# TEST 3: OVERSIZED NEW BUY
# --------------------------------------------------

print("\nTEST 3: OVERSIZED NEW BUY")
print("-" * 60)

oversized_buy = TradeDecision(
    asset="TSLA",
    action="BUY",
    confidence=0.90,
    position_size=1.0,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Strong positive event.",
)

approved, reason = risk_engine.evaluate(
    decision=oversized_buy,
    current_positions=portfolio,
)

print("Approved:", approved)
print("Reason:", reason)


# --------------------------------------------------
# TEST 4: DUPLICATE NVDA BUY
# --------------------------------------------------

print("\nTEST 4: DUPLICATE NVDA BUY")
print("-" * 60)

duplicate_buy = TradeDecision(
    asset="NVDA",
    action="BUY",
    confidence=0.90,
    position_size=0.05,
    stop_loss=0.05,
    take_profit=0.10,
    reasoning="Positive NVDA event.",
)

approved, reason = risk_engine.evaluate(
    decision=duplicate_buy,
    current_positions=portfolio,
)

print("Approved:", approved)
print("Reason:", reason)


# --------------------------------------------------
# TEST 5: HOLD
# --------------------------------------------------

print("\nTEST 5: HOLD")
print("-" * 60)

hold_decision = TradeDecision(
    asset="NVDA",
    action="HOLD",
    confidence=0.90,
    position_size=0.0,
    stop_loss=0.0,
    take_profit=0.0,
    reasoning="Existing NVDA position should be maintained.",
)

approved, reason = risk_engine.evaluate(
    decision=hold_decision,
    current_positions=portfolio,
)

print("Approved:", approved)
print("Reason:", reason)


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

print("\n" + "=" * 60)
print("TEST COMPLETE")
print("=" * 60)