import json
import os
from datetime import datetime


class TradeJournal:

    FILE_PATH = "data/trades.json"

    def __init__(self):

        self.trades = []

        self._load()

    # --------------------------------
    # LOAD EXISTING TRADES
    # --------------------------------

    def _load(self):

        if not os.path.exists(self.FILE_PATH):

            return

        try:

            with open(
                self.FILE_PATH,
                "r",
                encoding="utf-8",
            ) as file:

                self.trades = json.load(file)

        except (
            json.JSONDecodeError,
            OSError,
        ):

            self.trades = []

    # --------------------------------
    # SAVE TRADES
    # --------------------------------

    def _save(self):

        os.makedirs(
            os.path.dirname(self.FILE_PATH),
            exist_ok=True,
        )

        with open(
            self.FILE_PATH,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                self.trades,
                file,
                indent=4,
                default=str,
            )

    # --------------------------------
    # RECORD TRADE
    # --------------------------------

    def record(
        self,
        event,
        decision,
        approved,
        risk_reason,
        execution_result,
    ):

        trade = {
            "timestamp": datetime.now().isoformat(),

            "event": event.model_dump()
            if hasattr(event, "model_dump")
            else event,

            "asset": decision.asset,

            "action": decision.action,

            "confidence": decision.confidence,

            "position_size": decision.position_size,

            "stop_loss": decision.stop_loss,

            "take_profit": decision.take_profit,

            "reasoning": decision.reasoning,

            "risk_approved": approved,

            "risk_reason": risk_reason,

            "execution": execution_result,
        }

        self.trades.append(trade)

        self._save()

    # --------------------------------
    # SHOW JOURNAL
    # --------------------------------

    def show(self):

        if not self.trades:

            print("No trades recorded.")

            return

        for trade in self.trades:

            print("\n--- TRADE RECORD ---")

            for key, value in trade.items():

                print(
                    f"{key}: {value}"
                )

    # --------------------------------
    # NUMBER OF TRADES
    # --------------------------------

    def count(self):

        return len(self.trades)