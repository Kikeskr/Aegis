import json
import os

from agent.schemas import TradeDecision


class PaperTrader:

    STATE_FILE = "data/portfolio.json"

    def __init__(self, starting_balance: float = 10_000.0):

        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.positions = {}
        self.realized_pnl = 0.0

        self.equity_curve = [
            starting_balance
        ]

        self.trade_history = []

        self._load_state()

    # --------------------------------
    # LOAD PORTFOLIO STATE
    # --------------------------------

    def _load_state(self):

        if not os.path.exists(self.STATE_FILE):
            return

        try:

            with open(
                self.STATE_FILE,
                "r",
                encoding="utf-8",
            ) as file:

                state = json.load(file)

            self.balance = state.get(
                "balance",
                self.starting_balance,
            )

            self.positions = state.get(
                "positions",
                {},
            )

            self.realized_pnl = state.get(
                "realized_pnl",
                0.0,
            )

            self.equity_curve = state.get(
                "equity_curve",
                [self.starting_balance],
            )

            self.trade_history = state.get(
                "trade_history",
                [],
            )

            # --------------------------------
            # BACKWARD COMPATIBILITY
            # --------------------------------

            for asset, position in self.positions.items():

                if "side" not in position:

                    position["side"] = "LONG"

            print(
                f"Portfolio recovered: "
                f"${self.balance:.2f} cash"
            )

        except (
            json.JSONDecodeError,
            OSError,
        ):

            print(
                "Warning: Could not load portfolio state."
            )

            print(
                "Starting with a fresh portfolio."
            )

    # --------------------------------
    # SAVE PORTFOLIO STATE
    # --------------------------------

    def _save_state(self):

        directory = os.path.dirname(
            self.STATE_FILE
        )

        if directory:

            os.makedirs(
                directory,
                exist_ok=True,
            )

        state = {
            "balance": self.balance,
            "positions": self.positions,
            "realized_pnl": self.realized_pnl,
            "equity_curve": self.equity_curve,
            "trade_history": self.trade_history,
        }

        with open(
            self.STATE_FILE,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                state,
                file,
                indent=4,
            )

    # --------------------------------
    # EXECUTE TRADE
    # --------------------------------

    def execute(
        self,
        decision: TradeDecision,
        price: float,
    ):

        if decision.action == "HOLD":

            return "No trade executed."

        if price <= 0:

            return (
                "Trade rejected: "
                "price must be greater than zero."
            )

        # --------------------------------
        # BUY
        # --------------------------------

        if decision.action == "BUY":

            # --------------------------------
            # BUY TO COVER SHORT
            # --------------------------------

            if decision.asset in self.positions:

                position = self.positions[
                    decision.asset
                ]

                side = position.get(
                    "side",
                    "LONG",
                )

                if side == "SHORT":

                    quantity = position[
                        "quantity"
                    ]

                    entry_price = position[
                        "entry_price"
                    ]

                    cost = quantity * price

                    if cost > self.balance:

                        return (
                            "BUY TO COVER rejected: "
                            "insufficient cash."
                        )

                    pnl = (
                        quantity
                        * (entry_price - price)
                    )

                    self.balance -= cost

                    self.realized_pnl += pnl

                    self.positions.pop(
                        decision.asset
                    )

                    self.trade_history.append(
                        {
                            "status": "EXECUTED",
                            "asset": decision.asset,
                            "action": "BUY",
                            "side": "SHORT_COVER",
                            "quantity": quantity,
                            "price": price,
                            "pnl": pnl,
                        }
                    )

                    self._save_state()

                    return (
                        f"BUY TO COVER executed: "
                        f"{quantity:.4f} shares of "
                        f"{decision.asset} "
                        f"at ${price:.2f}. "
                        f"Realized P&L: "
                        f"${pnl:.2f}"
                    )

                # Existing LONG position

                return (
                    f"BUY rejected: "
                    f"{decision.asset} position "
                    f"already exists."
                )

            # --------------------------------
            # OPEN LONG POSITION
            # --------------------------------

            position_value = (
                self.balance
                * decision.position_size
            )

            if position_value <= 0:

                return (
                    "BUY rejected: "
                    "position size must be greater than zero."
                )

            if position_value > self.balance:

                return (
                    "BUY rejected: "
                    "insufficient cash."
                )

            quantity = (
                position_value / price
            )

            self.balance -= position_value

            self.positions[decision.asset] = {
                "quantity": quantity,
                "entry_price": price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "side": "LONG",
            }

            self.trade_history.append(
                {
                    "status": "EXECUTED",
                    "asset": decision.asset,
                    "action": "BUY",
                    "side": "LONG",
                    "quantity": quantity,
                    "price": price,
                }
            )

            self._save_state()

            return (
                f"BUY executed: "
                f"{quantity:.4f} shares of "
                f"{decision.asset} "
                f"at ${price:.2f}"
            )

        # --------------------------------
        # SELL
        # --------------------------------

        if decision.action == "SELL":

            # --------------------------------
            # CLOSE EXISTING LONG
            # --------------------------------

            if decision.asset in self.positions:

                position = self.positions[
                    decision.asset
                ]

                side = position.get(
                    "side",
                    "LONG",
                )

                if side == "LONG":

                    quantity = position[
                        "quantity"
                    ]

                    entry_price = position[
                        "entry_price"
                    ]

                    proceeds = (
                        quantity * price
                    )

                    cost = (
                        quantity * entry_price
                    )

                    pnl = (
                        proceeds - cost
                    )

                    self.balance += proceeds

                    self.realized_pnl += pnl

                    self.positions.pop(
                        decision.asset
                    )

                    self.trade_history.append(
                        {
                            "status": "EXECUTED",
                            "asset": decision.asset,
                            "action": "SELL",
                            "side": "LONG_EXIT",
                            "quantity": quantity,
                            "price": price,
                            "pnl": pnl,
                        }
                    )

                    self._save_state()

                    return (
                        f"SELL executed: "
                        f"{quantity:.4f} shares of "
                        f"{decision.asset} "
                        f"at ${price:.2f}. "
                        f"Realized P&L: "
                        f"${pnl:.2f}"
                    )

                return (
                    f"SELL rejected: "
                    f"{decision.asset} is already "
                    f"a SHORT position."
                )

            # --------------------------------
            # OPEN SHORT POSITION
            # --------------------------------

            position_value = (
                self.balance
                * decision.position_size
            )

            if position_value <= 0:

                return (
                    "SHORT rejected: "
                    "position size must be greater than zero."
                )

            quantity = (
                position_value / price
            )

            # Short sale proceeds enter cash.
            proceeds = (
                quantity * price
            )

            self.balance += proceeds

            self.positions[decision.asset] = {
                "quantity": quantity,
                "entry_price": price,
                "stop_loss": decision.stop_loss,
                "take_profit": decision.take_profit,
                "side": "SHORT",
            }

            self.trade_history.append(
                {
                    "status": "EXECUTED",
                    "asset": decision.asset,
                    "action": "SELL",
                    "side": "SHORT",
                    "quantity": quantity,
                    "price": price,
                }
            )

            self._save_state()

            return (
                f"SHORT SELL executed: "
                f"{quantity:.4f} shares of "
                f"{decision.asset} "
                f"at ${price:.2f}"
            )

        return "Trade not executed."

    # --------------------------------
    # CHECK STOP LOSS / TAKE PROFIT
    # --------------------------------

    def check_exit(
        self,
        asset: str,
        current_price: float,
    ):

        if asset not in self.positions:

            return (
                False,
                "No open position."
            )

        position = self.positions[asset]

        entry_price = position[
            "entry_price"
        ]

        stop_loss = position.get(
            "stop_loss",
            0.0,
        )

        take_profit = position.get(
            "take_profit",
            0.0,
        )

        side = position.get(
            "side",
            "LONG",
        )

        # --------------------------------
        # LONG EXIT LEVELS
        # --------------------------------

        if side == "LONG":

            stop_price = (
                entry_price
                * (1 - stop_loss)
            )

            take_profit_price = (
                entry_price
                * (1 + take_profit)
            )

            # --------------------------------
            # LONG STOP LOSS
            # --------------------------------

            if current_price <= stop_price:

                decision = TradeDecision(
                    asset=asset,
                    action="SELL",
                    confidence=1.0,
                    position_size=1.0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=(
                        "Automatic stop-loss exit."
                    ),
                )

                result = self.execute(
                    decision=decision,
                    price=current_price,
                )

                return (
                    True,
                    f"STOP_LOSS triggered. "
                    f"{result}"
                )

            # --------------------------------
            # LONG TAKE PROFIT
            # --------------------------------

            if current_price >= take_profit_price:

                decision = TradeDecision(
                    asset=asset,
                    action="SELL",
                    confidence=1.0,
                    position_size=1.0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=(
                        "Automatic take-profit exit."
                    ),
                )

                result = self.execute(
                    decision=decision,
                    price=current_price,
                )

                return (
                    True,
                    f"TAKE_PROFIT triggered. "
                    f"{result}"
                )

        # --------------------------------
        # SHORT EXIT LEVELS
        # --------------------------------

        if side == "SHORT":

            stop_price = (
                entry_price
                * (1 + stop_loss)
            )

            take_profit_price = (
                entry_price
                * (1 - take_profit)
            )

            # --------------------------------
            # SHORT STOP LOSS
            # --------------------------------

            if current_price >= stop_price:

                decision = TradeDecision(
                    asset=asset,
                    action="BUY",
                    confidence=1.0,
                    position_size=1.0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=(
                        "Automatic short "
                        "stop-loss exit."
                    ),
                )

                result = self.execute(
                    decision=decision,
                    price=current_price,
                )

                return (
                    True,
                    f"SHORT STOP_LOSS triggered. "
                    f"{result}"
                )

            # --------------------------------
            # SHORT TAKE PROFIT
            # --------------------------------

            if current_price <= take_profit_price:

                decision = TradeDecision(
                    asset=asset,
                    action="BUY",
                    confidence=1.0,
                    position_size=1.0,
                    stop_loss=stop_loss,
                    take_profit=take_profit,
                    reasoning=(
                        "Automatic short "
                        "take-profit exit."
                    ),
                )

                result = self.execute(
                    decision=decision,
                    price=current_price,
                )

                return (
                    True,
                    f"SHORT TAKE_PROFIT triggered. "
                    f"{result}"
                )

        return (
            False,
            "No exit triggered."
        )

    # --------------------------------
    # PORTFOLIO VALUE
    # --------------------------------

    def portfolio_value(
        self,
        current_prices: dict[str, float],
    ) -> float:

        total_value = self.balance

        for asset, position in self.positions.items():

            if asset not in current_prices:
                continue

            quantity = position[
                "quantity"
            ]

            current_price = current_prices[
                asset
            ]

            side = position.get(
                "side",
                "LONG",
            )

            # LONG positions add market value
            if side == "LONG":

                total_value += (
                    quantity
                    * current_price
                )

            # SHORT positions represent
            # a liability that must be bought back
            elif side == "SHORT":

                total_value -= (
                    quantity
                    * current_price
                )

        return total_value

    # --------------------------------
    # UNREALIZED P&L
    # --------------------------------

    def unrealized_pnl(
        self,
        current_prices: dict[str, float],
    ) -> float:

        pnl = 0.0

        for asset, position in self.positions.items():

            if asset not in current_prices:
                continue

            quantity = position[
                "quantity"
            ]

            entry_price = position[
                "entry_price"
            ]

            current_price = current_prices[
                asset
            ]

            side = position.get(
                "side",
                "LONG",
            )

            if side == "LONG":

                pnl += (
                    quantity
                    * (
                        current_price
                        - entry_price
                    )
                )

            elif side == "SHORT":

                pnl += (
                    quantity
                    * (
                        entry_price
                        - current_price
                    )
                )

        return pnl

    # --------------------------------
    # TOTAL P&L
    # --------------------------------

    def total_pnl(
        self,
        current_prices: dict[str, float],
    ) -> float:

        return (
            self.realized_pnl
            + self.unrealized_pnl(
                current_prices
            )
        )

    # --------------------------------
    # RECORD EQUITY
    # --------------------------------

    def record_equity(
        self,
        current_prices: dict[str, float],
    ) -> float:

        equity = self.portfolio_value(
            current_prices
        )

        self.equity_curve.append(
            equity
        )

        self._save_state()

        return equity

    # --------------------------------
    # GET OPEN POSITIONS
    # --------------------------------

    def get_open_positions(self):

        return self.positions

    # --------------------------------
    # RESET PORTFOLIO
    # --------------------------------

    def reset(self):

        self.balance = (
            self.starting_balance
        )

        self.positions = {}

        self.realized_pnl = 0.0

        self.equity_curve = [
            self.starting_balance
        ]

        self.trade_history = []

        self._save_state()

        print(
            "Portfolio reset successfully."
        )