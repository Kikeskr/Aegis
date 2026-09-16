from agent.events import MarketEvent
from agent.qwen_agent import analyze_event
from execution.paper_trader import PaperTrader


print("=" * 60)
print("AEGIS PORTFOLIO AWARENESS TEST")
print("=" * 60)

trader = PaperTrader(starting_balance=10_000)

print("\nCURRENT PORTFOLIO")
print("-" * 60)

if not trader.positions:
    print("No open positions.")
else:
    for asset, position in trader.positions.items():
        print(f"{asset}: {position}")


event = MarketEvent(
    event_type="EARNINGS",
    description=(
        "NVIDIA reports strong earnings and raises its outlook, "
        "suggesting continued demand for AI chips."
    ),
    sentiment="POSITIVE",
    impact="HIGH",
    affected_assets=["NVDA"],
)

print("\nTEST EVENT")
print("-" * 60)
print(event)


print("\nASKING QWEN FOR A TRADE DECISION...")
print("-" * 60)

decision = analyze_event(
    event=event,
    current_positions=trader.positions,
)

print("\nQWEN DECISION")
print("-" * 60)
print(decision)


print("\nPORTFOLIO AWARENESS RESULT")
print("-" * 60)

if "NVDA" in trader.positions:
    current_side = trader.positions["NVDA"].get("side")

    print(f"Existing NVDA position: {current_side}")
    print(f"Qwen action: {decision.action}")

    if current_side == "LONG" and decision.action == "BUY":
        print("\nWARNING: Qwen attempted to BUY an existing NVDA LONG.")
        print("Portfolio-awareness test FAILED.")
    else:
        print("\nQwen respected the existing NVDA position.")
        print("Portfolio-awareness test PASSED.")

else:
    print("No NVDA position exists.")
    print("The test cannot verify the existing-position rule.")