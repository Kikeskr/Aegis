import json

from sqlalchemy.orm import Session

from agent.event_filter import EventFilter
from agent.events import MarketEvent
from agent.qwen_agent import analyze_event
from agent.price_feed import PriceFeed
from execution.database_paper_trader import DatabasePaperTrader
from risk.risk_engine import RiskEngine

from api import models
from api.models import PaperWallet


class AegisService:
    def __init__(self, db: Session, wallet: PaperWallet):
        self.db = db
        self.wallet = wallet

        self.event_filter = EventFilter()
        self.risk_engine = RiskEngine()
        self.price_feed = PriceFeed()

        self.trader = DatabasePaperTrader(
            db=db,
            wallet=wallet,
        )

    def get_positions(self) -> dict:
        return self.trader.get_positions()

    def record_event(
        self,
        event: MarketEvent,
        filter_result: dict,
        decision: dict | None = None,
        risk: dict | None = None,
        execution: dict | None = None,
        portfolio: dict | None = None,
    ):
        """
        Save the complete Aegis event-processing chain
        for the current user's wallet.
        """

        event_record = models.EventRecord(
            wallet_id=self.wallet.id,
            event_type=event.event_type,
            description=event.description,
            sentiment=event.sentiment,
            impact=event.impact,
            affected_assets=json.dumps(
                event.affected_assets
            ),
            filter_approved=filter_result.get(
                "approved",
                False,
            ),
            filter_reason=filter_result.get(
                "reason",
                "",
            ),
            decision_json=(
                json.dumps(decision)
                if decision is not None
                else None
            ),
            risk_json=(
                json.dumps(risk)
                if risk is not None
                else None
            ),
            execution_json=(
                json.dumps(execution)
                if execution is not None
                else None
            ),
            portfolio_json=(
                json.dumps(portfolio)
                if portfolio is not None
                else None
            ),
        )

        self.db.add(event_record)
        self.db.commit()

        print(
            "[AEGIS EVENT] Event recorded in Event Intelligence."
        )

    def process_event(
        self,
        event: MarketEvent,
    ) -> dict:

        # ========================================================
        # 1. EVENT FILTER
        # ========================================================

        approved, filter_reason = (
            self.event_filter.evaluate(event)
        )

        filter_result = {
            "approved": approved,
            "reason": filter_reason,
        }

        if not approved:

            result = {
                "event": event.model_dump(),
                "filter": filter_result,
                "decision": None,
                "risk": None,
                "execution": None,
                "portfolio": None,
            }

            self.record_event(
                event=event,
                filter_result=filter_result,
            )

            return result

        # ========================================================
        # 2. CURRENT POSITIONS
        # ========================================================

        current_positions = (
            self.trader.get_positions()
        )

        # ========================================================
        # 3. QWEN DECISION
        # ========================================================

        decision = analyze_event(
            event=event,
            current_positions=current_positions,
        )

        decision_data = decision.model_dump()

        # ========================================================
        # 4. RISK ENGINE
        # ========================================================

        risk_approved, risk_reason = (
            self.risk_engine.evaluate(
                decision=decision,
                current_positions=current_positions,
            )
        )

        risk_result = {
            "approved": risk_approved,
            "reason": risk_reason,
        }

        if not risk_approved:

            result = {
                "event": event.model_dump(),
                "filter": filter_result,
                "decision": decision_data,
                "risk": risk_result,
                "execution": None,
                "portfolio": None,
            }

            self.record_event(
                event=event,
                filter_result=filter_result,
                decision=decision_data,
                risk=risk_result,
            )

            return result

        # ========================================================
        # 5. HOLD
        # ========================================================

        if decision.action == "HOLD":

            execution_result = {
                "executed": False,
                "message": "No trade executed.",
            }

            result = {
                "event": event.model_dump(),
                "filter": filter_result,
                "decision": decision_data,
                "risk": risk_result,
                "execution": execution_result,
                "portfolio": None,
            }

            self.record_event(
                event=event,
                filter_result=filter_result,
                decision=decision_data,
                risk=risk_result,
                execution=execution_result,
            )

            return result

        # ========================================================
        # 6. MARKET PRICE
        # ========================================================

        market_price = self.price_feed.get_price(
            decision.asset
        )

        # ========================================================
        # 7. PAPER TRADE EXECUTION
        # ========================================================

        execution_message = self.trader.execute(
            decision=decision,
            price=market_price,
        )

        executed = not execution_message.lower().startswith(
            "no trade executed"
        )

        execution_result = {
            "executed": executed,
            "message": execution_message,
            "price": market_price,
        }

        # ========================================================
        # 8. UPDATE EQUITY
        # ========================================================

        current_prices = {}

        for asset in self.trader.get_positions():

            current_prices[asset] = (
                self.price_feed.get_price(asset)
            )

        equity = self.trader.record_equity(
            current_prices=current_prices
        )

        portfolio_result = {
            "equity": equity,
        }

        # ========================================================
        # 9. COMPLETE RESULT
        # ========================================================

        result = {
            "event": event.model_dump(),
            "filter": filter_result,
            "decision": decision_data,
            "risk": risk_result,
            "execution": execution_result,
            "portfolio": portfolio_result,
        }

        # ========================================================
        # 10. SAVE TO EVENT INTELLIGENCE
        # ========================================================

        self.record_event(
            event=event,
            filter_result=filter_result,
            decision=decision_data,
            risk=risk_result,
            execution=execution_result,
            portfolio=portfolio_result,
        )

        return result

    def monitor_positions(self) -> list[dict]:

        results = []

        positions = list(
            self.trader.get_positions().keys()
        )

        for asset in positions:

            current_price = (
                self.price_feed.get_price(asset)
            )

            triggered, message = (
                self.trader.check_exit(
                    asset=asset,
                    current_price=current_price,
                )
            )

            results.append(
                {
                    "asset": asset,
                    "price": current_price,
                    "exit_triggered": triggered,
                    "message": message,
                }
            )

        return results