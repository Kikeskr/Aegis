import math


class PerformanceEngine:

    def __init__(self, starting_balance: float):
        self.starting_balance = starting_balance

    def total_return(self, equity_curve: list[float]) -> float:

        if not equity_curve:
            return 0.0

        final_equity = equity_curve[-1]

        return (
            (final_equity - self.starting_balance)
            / self.starting_balance
        )

    def max_drawdown(self, equity_curve: list[float]) -> float:

        if not equity_curve:
            return 0.0

        peak = equity_curve[0]
        max_drawdown = 0.0

        for equity in equity_curve:

            if equity > peak:
                peak = equity

            if peak <= 0:
                continue

            drawdown = (peak - equity) / peak

            if drawdown > max_drawdown:
                max_drawdown = drawdown

        return max_drawdown

    def win_rate(self, trade_history: list[dict]) -> float:

        # Only count trades that actually close a position.
        #
        # LONG_EXIT   = closes a long position
        # SHORT_COVER = closes a short position
        completed_trades = [
            trade
            for trade in trade_history
            if trade.get("side") in {
                "LONG_EXIT",
                "SHORT_COVER",
            }
            and trade.get("status") == "EXECUTED"
        ]

        if not completed_trades:
            return 0.0

        winning_trades = [
            trade
            for trade in completed_trades
            if trade.get("pnl", 0.0) > 0
        ]

        return (
            len(winning_trades)
            / len(completed_trades)
        )

    def sharpe_ratio(
        self,
        equity_curve: list[float],
    ) -> float:

        if len(equity_curve) < 2:
            return 0.0

        returns = []

        for i in range(1, len(equity_curve)):

            previous = equity_curve[i - 1]
            current = equity_curve[i]

            if previous <= 0:
                continue

            period_return = (
                current - previous
            ) / previous

            returns.append(period_return)

        if len(returns) < 2:
            return 0.0

        mean_return = sum(returns) / len(returns)

        variance = sum(
            (r - mean_return) ** 2
            for r in returns
        ) / len(returns)

        standard_deviation = math.sqrt(variance)

        if standard_deviation == 0:
            return 0.0

        return (
            mean_return
            / standard_deviation
        ) * math.sqrt(len(returns))