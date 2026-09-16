from agent.schemas import TradeDecision


class RiskEngine:

    def __init__(
        self,
        max_position_size: float = 0.10,
        max_trade_risk: float = 0.01,
        minimum_confidence: float = 0.50,
        max_stop_loss: float = 0.20,
    ):
        self.max_position_size = max_position_size
        self.max_trade_risk = max_trade_risk
        self.minimum_confidence = minimum_confidence
        self.max_stop_loss = max_stop_loss

    def evaluate(
        self,
        decision: TradeDecision,
        current_positions: dict | None = None,
    ) -> tuple[bool, str]:

        if current_positions is None:
            current_positions = {}

        # --------------------------------------------------
        # 1. VALIDATE ACTION
        # --------------------------------------------------

        if decision.action not in {
            "BUY",
            "SELL",
            "HOLD",
        }:
            return False, "Invalid trading action."

        # --------------------------------------------------
        # 2. HOLD
        # --------------------------------------------------

        if decision.action == "HOLD":

            if decision.position_size != 0:
                return (
                    False,
                    "HOLD decision must have zero position size.",
                )

            if decision.stop_loss != 0:
                return (
                    False,
                    "HOLD decision must have zero stop loss.",
                )

            if decision.take_profit != 0:
                return (
                    False,
                    "HOLD decision must have zero take profit.",
                )

            return True, "HOLD decision approved."

        # --------------------------------------------------
        # 3. CONFIDENCE
        # --------------------------------------------------

        if not 0.0 <= decision.confidence <= 1.0:
            return (
                False,
                "AI confidence must be between 0 and 1.",
            )

        if decision.confidence < self.minimum_confidence:
            return (
                False,
                "AI confidence is below the minimum threshold.",
            )

        # --------------------------------------------------
        # 4. CHECK EXISTING POSITION
        # --------------------------------------------------

        existing_position = current_positions.get(
            decision.asset
        )

        existing_side = None

        if existing_position:
            existing_side = existing_position.get("side")

        # --------------------------------------------------
        # 5. DETERMINE WHETHER THIS IS AN EXIT
        # --------------------------------------------------

        is_exit = (
            (decision.action == "SELL" and existing_side == "LONG")
            or
            (decision.action == "BUY" and existing_side == "SHORT")
        )

        # --------------------------------------------------
        # 6. EXIT RISK CHECK
        # --------------------------------------------------

        if is_exit:

            if decision.position_size <= 0:
                return (
                    False,
                    "Exit position size must be greater than zero.",
                )

            if decision.position_size > 1.0:
                return (
                    False,
                    "Exit position size cannot exceed 100%.",
                )

            return (
                True,
                (
                    "Position exit approved by risk engine. "
                    f"Closing {existing_side} position."
                ),
            )

        # --------------------------------------------------
        # 7. PREVENT CONFLICTING POSITIONS
        # --------------------------------------------------

        if existing_side == "LONG" and decision.action == "BUY":
            return (
                False,
                "BUY rejected: LONG position already exists.",
            )

        if existing_side == "SHORT" and decision.action == "SELL":
            return (
                False,
                "SELL rejected: SHORT position already exists.",
            )

        # --------------------------------------------------
        # 8. NORMAL POSITION SIZE
        # --------------------------------------------------

        if decision.position_size <= 0:
            return (
                False,
                "Position size must be greater than zero.",
            )

        if decision.position_size > self.max_position_size:
            return (
                False,
                "Position size exceeds the maximum allowed.",
            )

        # --------------------------------------------------
        # 9. STOP LOSS
        # --------------------------------------------------

        if decision.stop_loss <= 0:
            return (
                False,
                "Stop loss must be greater than zero.",
            )

        if decision.stop_loss > self.max_stop_loss:
            return (
                False,
                "Stop loss exceeds the maximum allowed.",
            )

        # --------------------------------------------------
        # 10. TAKE PROFIT
        # --------------------------------------------------

        if decision.take_profit <= 0:
            return (
                False,
                "Take profit must be greater than zero.",
            )

        if decision.take_profit <= decision.stop_loss:
            return (
                False,
                "Take profit must be greater than stop loss.",
            )

        # --------------------------------------------------
        # 11. RISK / REWARD
        # --------------------------------------------------

        risk_reward_ratio = (
            decision.take_profit
            / decision.stop_loss
        )

        if risk_reward_ratio < 1.0:
            return (
                False,
                "Risk/reward ratio is below 1:1.",
            )

        # --------------------------------------------------
        # 12. TRADE RISK
        # --------------------------------------------------

        trade_risk = (
            decision.position_size
            * decision.stop_loss
        )

        if trade_risk > self.max_trade_risk:
            return (
                False,
                "Trade risk exceeds the maximum allowed.",
            )

        # --------------------------------------------------
        # 13. APPROVE NEW POSITION
        # --------------------------------------------------

        return (
            True,
            (
                "Trade approved by risk engine. "
                f"Risk: {trade_risk * 100:.2f}%, "
                f"Position: {decision.position_size * 100:.2f}%, "
                f"R/R: {risk_reward_ratio:.2f}:1."
            ),
        )