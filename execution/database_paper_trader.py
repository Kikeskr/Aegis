from sqlalchemy.orm import Session

from agent.schemas import TradeDecision
from api.models import EquitySnapshot, PaperWallet, Position, Trade


class DatabasePaperTrader:
    """
    Database-backed paper trading engine.

    Each user has their own PaperWallet, positions, trades,
    and equity history.
    """

    def __init__(self, db: Session, wallet: PaperWallet):
        self.db = db
        self.wallet = wallet

    # ---------------------------------------------------------
    # POSITION HELPERS
    # ---------------------------------------------------------

    def get_positions(self) -> dict:
        """
        Return the user's current positions as a dictionary
        keyed by asset.
        """

        positions = (
            self.db.query(Position)
            .filter(Position.wallet_id == self.wallet.id)
            .all()
        )

        return {
            position.asset: {
                "id": position.id,
                "side": position.side,
                "quantity": position.quantity,
                "entry_price": position.entry_price,
                "stop_loss": position.stop_loss,
                "take_profit": position.take_profit,
            }
            for position in positions
        }

    def get_position(self, asset: str) -> Position | None:
        """
        Find an open position for a specific asset.
        """

        return (
            self.db.query(Position)
            .filter(
                Position.wallet_id == self.wallet.id,
                Position.asset == asset,
            )
            .first()
        )

    # ---------------------------------------------------------
    # RETURN CALCULATION
    # ---------------------------------------------------------

    @staticmethod
    def calculate_trade_return(
        pnl: float,
        entry_price: float,
        quantity: float,
    ) -> float:
        """
        Calculate percentage return for a closed trade.

        Formula:

            Return % =
                P&L / Capital Invested × 100

        Capital invested is based on the position's entry
        price multiplied by its quantity.
        """

        capital_invested = entry_price * quantity

        if capital_invested <= 0:
            return 0.0

        return (pnl / capital_invested) * 100

    def calculate_portfolio_return(
        self,
        equity: float,
    ) -> float:
        """
        Calculate overall portfolio percentage return.

        Formula:

            Return % =
                (Current Equity - Initial Capital)
                / Initial Capital × 100
        """

        initial_balance = self.wallet.initial_balance

        if initial_balance <= 0:
            return 0.0

        return (
            (equity - initial_balance)
            / initial_balance
        ) * 100

    # ---------------------------------------------------------
    # TRADE EXECUTION
    # ---------------------------------------------------------

    def execute(
        self,
        decision: TradeDecision,
        price: float,
    ) -> str:
        """
        Execute a paper trade based on an approved decision.

        BUY:
            - Open LONG if no position exists.
            - Close SHORT if a short position exists.

        SELL:
            - Close LONG if a long position exists.
            - Open SHORT if no position exists.

        HOLD:
            - No trade.
        """

        asset = decision.asset.upper()
        action = decision.action.upper()

        if action == "HOLD":
            return "No trade executed."

        existing_position = self.get_position(asset)

        # -----------------------------------------------------
        # BUY
        # -----------------------------------------------------

        if action == "BUY":

            # Cover an existing SHORT position.
            if existing_position:

                if existing_position.side == "SHORT":
                    return self._close_position(
                        position=existing_position,
                        price=price,
                        action="SHORT_EXIT",
                    )

                return "No trade executed: LONG position already exists."

            # Open a new LONG position.
            quantity = self._calculate_quantity(
                price=price,
                position_size=decision.position_size,
            )

            if quantity <= 0:
                return "No trade executed: insufficient balance."

            trade_value = price * quantity

            if trade_value > self.wallet.balance:
                return "No trade executed: insufficient balance."

            self.wallet.balance -= trade_value

            position = Position(
                wallet_id=self.wallet.id,
                asset=asset,
                side="LONG",
                quantity=quantity,
                entry_price=price,
                stop_loss=decision.stop_loss,
                take_profit=decision.take_profit,
            )

            self.db.add(position)

            trade = Trade(
                wallet_id=self.wallet.id,
                asset=asset,
                action="BUY",
                side="LONG",
                quantity=quantity,
                price=price,
                pnl=0.0,
                return_pct=0.0,
                status="OPEN",
                reasoning=decision.reasoning,
                confidence=decision.confidence,
            )

            self.db.add(trade)
            self.db.commit()

            return (
                f"BUY executed: "
                f"{quantity:.6f} {asset} "
                f"at ${price:.2f}."
            )

        # -----------------------------------------------------
        # SELL
        # -----------------------------------------------------

        if action == "SELL":

            # Close an existing LONG position.
            if existing_position:

                if existing_position.side == "LONG":
                    return self._close_position(
                        position=existing_position,
                        price=price,
                        action="LONG_EXIT",
                    )

                return "No trade executed: SHORT position already exists."

            # Open a new SHORT position.
            quantity = self._calculate_quantity(
                price=price,
                position_size=decision.position_size,
            )

            if quantity <= 0:
                return "No trade executed: insufficient balance."

            trade_value = price * quantity

            # Simplified paper-short accounting.
            self.wallet.balance += trade_value

            position = Position(
                wallet_id=self.wallet.id,
                asset=asset,
                side="SHORT",
                quantity=quantity,
                entry_price=price,
                stop_loss=decision.stop_loss,
                take_profit=decision.take_profit,
            )

            self.db.add(position)

            trade = Trade(
                wallet_id=self.wallet.id,
                asset=asset,
                action="SELL",
                side="SHORT",
                quantity=quantity,
                price=price,
                pnl=0.0,
                return_pct=0.0,
                status="OPEN",
                reasoning=decision.reasoning,
                confidence=decision.confidence,
            )

            self.db.add(trade)
            self.db.commit()

            return (
                f"SELL executed: "
                f"{quantity:.6f} {asset} "
                f"at ${price:.2f}."
            )

        return f"Unsupported action: {action}"

    # ---------------------------------------------------------
    # MANUAL CLOSE POSITION
    # ---------------------------------------------------------

    def close_position(
        self,
        position: Position,
        price: float,
    ) -> str:
        """
        Manually close an existing position.

        Uses the same closing and accounting path as
        automatic exits.
        """

        return self._close_position(
            position=position,
            price=price,
            action="MANUAL_EXIT",
        )

    # ---------------------------------------------------------
    # CLOSE POSITION
    # ---------------------------------------------------------

    def _close_position(
        self,
        position: Position,
        price: float,
        action: str,
    ) -> str:
        """
        Close an existing LONG or SHORT position.

        Calculates:
            - Dollar P&L
            - Percentage return
            - Updated wallet balance
            - Updated realized P&L
            - Closed trade record
        """

        quantity = position.quantity
        entry_price = position.entry_price

        # -----------------------------------------------------
        # LONG
        # -----------------------------------------------------

        if position.side == "LONG":

            pnl = (
                price - entry_price
            ) * quantity

            sale_value = price * quantity

            self.wallet.balance += sale_value

        # -----------------------------------------------------
        # SHORT
        # -----------------------------------------------------

        elif position.side == "SHORT":

            pnl = (
                entry_price - price
            ) * quantity

            buyback_cost = price * quantity

            self.wallet.balance -= buyback_cost

        else:
            return f"Unknown position side: {position.side}"

        # -----------------------------------------------------
        # PERCENTAGE RETURN
        # -----------------------------------------------------

        return_pct = self.calculate_trade_return(
            pnl=pnl,
            entry_price=entry_price,
            quantity=quantity,
        )

        self.wallet.realized_pnl += pnl

        # -----------------------------------------------------
        # RECORD CLOSED TRADE
        # -----------------------------------------------------

        trade = Trade(
            wallet_id=self.wallet.id,
            asset=position.asset,
            action=action,
            side=position.side,
            quantity=quantity,
            price=price,
            pnl=pnl,
            return_pct=return_pct,
            status="CLOSED",
            reasoning="Position closed.",
            confidence=1.0,
        )

        self.db.add(trade)

        # Remove the open position.
        self.db.delete(position)

        self.db.commit()

        sign = "+" if pnl >= 0 else ""
        return_sign = "+" if return_pct >= 0 else ""

        return (
            f"{action} executed: "
            f"{quantity:.6f} {position.asset} "
            f"at ${price:.2f}. "
            f"P&L: {sign}${pnl:.2f}. "
            f"Return: {return_sign}{return_pct:.2f}%."
        )

    # ---------------------------------------------------------
    # QUANTITY
    # ---------------------------------------------------------

    def _calculate_quantity(
        self,
        price: float,
        position_size: float,
    ) -> float:
        """
        Convert the requested portfolio percentage into
        an asset quantity.

        Example:

            Equity = $10,000
            Position size = 8%
            Capital = $800

            If price = $200:

            Quantity = 800 / 200
                     = 4 shares
        """

        if price <= 0:
            return 0.0

        equity = self.calculate_equity(
            current_prices={}
        )

        capital_to_use = equity * position_size

        if capital_to_use <= 0:
            return 0.0

        return capital_to_use / price

    # ---------------------------------------------------------
    # EXIT MONITORING
    # ---------------------------------------------------------

    def check_exit(
        self,
        asset: str,
        current_price: float,
    ) -> tuple[bool, str]:
        """
        Check whether a position has reached its stop loss
        or take profit.

        stop_loss and take_profit are interpreted as
        percentages.
        """

        position = self.get_position(asset)

        if not position:
            return False, "No open position."

        entry_price = position.entry_price

        # -----------------------------------------------------
        # LONG
        # -----------------------------------------------------

        if position.side == "LONG":

            stop_price = entry_price * (
                1 - position.stop_loss
            )

            take_profit_price = entry_price * (
                1 + position.take_profit
            )

            if current_price <= stop_price:

                message = self._close_position(
                    position=position,
                    price=current_price,
                    action="LONG_STOP",
                )

                return True, message

            if current_price >= take_profit_price:

                message = self._close_position(
                    position=position,
                    price=current_price,
                    action="LONG_TAKE_PROFIT",
                )

                return True, message

        # -----------------------------------------------------
        # SHORT
        # -----------------------------------------------------

        elif position.side == "SHORT":

            stop_price = entry_price * (
                1 + position.stop_loss
            )

            take_profit_price = entry_price * (
                1 - position.take_profit
            )

            if current_price >= stop_price:

                message = self._close_position(
                    position=position,
                    price=current_price,
                    action="SHORT_STOP",
                )

                return True, message

            if current_price <= take_profit_price:

                message = self._close_position(
                    position=position,
                    price=current_price,
                    action="SHORT_TAKE_PROFIT",
                )

                return True, message

        return False, "No exit condition triggered."

    # ---------------------------------------------------------
    # EQUITY
    # ---------------------------------------------------------

    def calculate_equity(
        self,
        current_prices: dict,
    ) -> float:
        """
        Calculate current portfolio equity.

        LONG:

            Equity contribution =
                quantity × current price

        SHORT:

            Equity contribution =
                -quantity × current price

        Cash balance already reflects the trade mechanics.
        """

        equity = self.wallet.balance

        positions = (
            self.db.query(Position)
            .filter(Position.wallet_id == self.wallet.id)
            .all()
        )

        for position in positions:

            current_price = current_prices.get(
                position.asset
            )

            if current_price is None:
                current_price = position.entry_price

            if position.side == "LONG":

                equity += (
                    position.quantity
                    * current_price
                )

            elif position.side == "SHORT":

                equity -= (
                    position.quantity
                    * current_price
                )

        return equity

    # ---------------------------------------------------------
    # EQUITY SNAPSHOT
    # ---------------------------------------------------------

    def record_equity(
        self,
        current_prices: dict,
    ) -> float:
        """
        Calculate and persist the current portfolio equity.
        """

        equity = self.calculate_equity(
            current_prices=current_prices
        )

        snapshot = EquitySnapshot(
            wallet_id=self.wallet.id,
            equity=equity,
        )

        self.db.add(snapshot)
        self.db.commit()

        return equity