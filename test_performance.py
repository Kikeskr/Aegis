from performance.performance_engine import PerformanceEngine


# Starting account balance
starting_balance = 10_000

engine = PerformanceEngine(
    starting_balance=starting_balance
)


# Simulated equity history
equity_curve = [
    10_000,
    10_200,
    10_100,
    10_400,
    10_300,
    10_600,
]


# Simulated completed trades
trade_history = [
    {
        "asset": "AAPL",
        "action": "BUY",
        "quantity": 10,
        "price": 100,
    },
    {
        "asset": "AAPL",
        "action": "SELL",
        "quantity": 10,
        "price": 120,
        "pnl": 200,
    },
    {
        "asset": "NVDA",
        "action": "BUY",
        "quantity": 5,
        "price": 200,
    },
    {
        "asset": "NVDA",
        "action": "SELL",
        "quantity": 5,
        "price": 190,
        "pnl": -50,
    },
]


# Calculate metrics

total_return = engine.total_return(
    equity_curve
)

max_drawdown = engine.max_drawdown(
    equity_curve
)

win_rate = engine.win_rate(
    trade_history
)

sharpe = engine.sharpe_ratio(
    equity_curve
)


# Display results

print("\n" + "=" * 50)
print("AEGIS PERFORMANCE TEST")
print("=" * 50)

print(
    f"Total Return: "
    f"{total_return * 100:.2f}%"
)

print(
    f"Maximum Drawdown: "
    f"{max_drawdown * 100:.2f}%"
)

print(
    f"Win Rate: "
    f"{win_rate * 100:.2f}%"
)

print(
    f"Sharpe Ratio: "
    f"{sharpe:.4f}"
)