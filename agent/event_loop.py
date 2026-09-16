from agent.event_memory import EventMemory
from agent.event_filter import EventFilter
from agent.price_feed import PriceFeed
from agent.qwen_agent import analyze_event, classify_news
from execution.paper_trader import PaperTrader
from journal.trade_journal import TradeJournal
from performance.performance_engine import PerformanceEngine
from risk.risk_engine import RiskEngine


class EventLoop:

    def __init__(self):

        self.event_filter = EventFilter()
        self.risk_engine = RiskEngine()

        self.trader = PaperTrader(
            starting_balance=10_000
        )

        self.performance = PerformanceEngine(
            starting_balance=10_000
        )

        self.journal = TradeJournal()
        self.price_feed = PriceFeed()
        self.event_memory = EventMemory()

    # ========================================
    # PROCESS ONE NEWS ARTICLE
    # ========================================

    def process_article(self, article: dict):

        article_url = article.get("url", "").strip()

        # --------------------------------
        # CHECK EVENT MEMORY
        # --------------------------------

        if self.event_memory.is_processed(article):

            print("\n" + "-" * 60)
            print("DUPLICATE EVENT")
            print("-" * 60)
            print("Title:", article.get("title", ""))
            print("Action: Already processed. Skipping.")

            return

        print("\n" + "=" * 60)
        print("NEWS ARTICLE")
        print("=" * 60)

        print("Title:", article["title"])

        # --------------------------------
        # 1. CLASSIFY NEWS
        # --------------------------------

        event = classify_news(
            title=article["title"],
            summary=article["summary"],
        )

        print("\nMARKET EVENT")
        print(event)

        # --------------------------------
        # 2. FILTER EVENT
        # --------------------------------

        approved, filter_reason = (
            self.event_filter.evaluate(event)
        )

        print("\nEVENT FILTER")
        print("Approved:", approved)
        print("Reason:", filter_reason)

        # --------------------------------
        # REMEMBER FILTERED EVENTS
        # --------------------------------

        if not approved:

            self.event_memory.mark_processed(article)

            print("\nACTION: Event ignored.")
            print("Event recorded in event memory.")

            return

        # --------------------------------
        # 3. GENERATE TRADE DECISION
        # --------------------------------

        decision = analyze_event(
            event=event,
            current_positions=self.trader.positions,
        )

        print("\nTRADE DECISION")
        print(decision)

        # --------------------------------
        # 4. RISK ENGINE
        # --------------------------------

        risk_approved, risk_reason = self.risk_engine.evaluate(
            decision=decision,
            current_positions=self.trader.positions,
        )
        
        print("\nRISK ENGINE")
        print("Approved:", risk_approved)
        print("Reason:", risk_reason)

        if not risk_approved:

            self.event_memory.mark_processed(article)

            print("\nACTION: Trade rejected.")
            print("Event recorded in event memory.")

            return

        # --------------------------------
        # 5. GET MARKET PRICE
        # --------------------------------

        market_price = self.price_feed.get_price(
            decision.asset
        )

        print("\nMARKET PRICE")
        print(
            f"{decision.asset}: "
            f"${market_price:.2f}"
        )

        # --------------------------------
        # 6. PAPER EXECUTION
        # --------------------------------

        execution_result = self.trader.execute(
            decision=decision,
            price=market_price,
        )

        print("\nPAPER EXECUTION")
        print(execution_result)

        # --------------------------------
        # 7. RECORD EQUITY
        # --------------------------------

        current_prices = {}

        for asset in self.trader.positions:

            current_prices[asset] = (
                self.price_feed.get_price(asset)
            )

        equity = self.trader.record_equity(
            current_prices
        )

        print("\nPORTFOLIO EQUITY")
        print(f"${equity:.2f}")

        # --------------------------------
        # 8. TRADE JOURNAL
        # --------------------------------

        self.journal.record(
            event=event,
            decision=decision,
            approved=risk_approved,
            risk_reason=risk_reason,
            execution_result=execution_result,
        )

        # --------------------------------
        # 9. REMEMBER PROCESSED EVENT
        # --------------------------------

        self.event_memory.mark_processed(article)

        print("\nEVENT PROCESSING COMPLETE")
        print("Event recorded in event memory.")

    # ========================================
    # MONITOR OPEN POSITIONS
    # ========================================

    def monitor_positions(self):

        print("\n" + "=" * 60)
        print("AEGIS POSITION MONITOR")
        print("=" * 60)

        # --------------------------------
        # NO OPEN POSITIONS
        # --------------------------------

        if not self.trader.positions:

            print("\nNo open positions.")

            equity = self.trader.record_equity({})

            print(
                f"\nPortfolio equity: "
                f"${equity:.2f}"
            )

            return

        # --------------------------------
        # CHECK OPEN POSITIONS
        # --------------------------------

        current_prices = {}

        for asset in list(
            self.trader.positions.keys()
        ):

            current_price = self.price_feed.get_price(
                asset
            )

            current_prices[asset] = current_price

            print(
                f"\n{asset} current price: "
                f"${current_price:.2f}"
            )

            # --------------------------------
            # CHECK EXIT CONDITIONS
            # --------------------------------

            exit_triggered, exit_message = (
                self.trader.check_exit(
                    asset=asset,
                    current_price=current_price,
                )
            )

            if exit_triggered:

                print("\nEXIT TRIGGERED")
                print(exit_message)

            else:

                print("\nNo exit triggered.")

        # --------------------------------
        # REFRESH PRICES AFTER EXITS
        # --------------------------------

        current_prices = {}

        for asset in list(
            self.trader.positions.keys()
        ):

            current_prices[asset] = (
                self.price_feed.get_price(asset)
            )

        # --------------------------------
        # RECORD CURRENT EQUITY
        # --------------------------------

        equity = self.trader.record_equity(
            current_prices
        )

        print(
            f"\nPortfolio equity: "
            f"${equity:.2f}"
        )

    # ========================================
    # DISPLAY PERFORMANCE
    # ========================================

    def display_performance(self):

        print("\n" + "=" * 60)
        print("AEGIS PERFORMANCE")
        print("=" * 60)

        equity_curve = self.trader.equity_curve
        trade_history = self.trader.trade_history

        total_return = self.performance.total_return(
            equity_curve
        )

        max_drawdown = self.performance.max_drawdown(
            equity_curve
        )

        win_rate = self.performance.win_rate(
            trade_history
        )

        sharpe = self.performance.sharpe_ratio(
            equity_curve
        )

        print("\nPERFORMANCE")

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

    # ========================================
    # DISPLAY TRADE JOURNAL
    # ========================================

    def display_journal(self):

        print("\n" + "=" * 60)
        print("AEGIS TRADE JOURNAL")
        print("=" * 60)

        self.journal.show()

    # ========================================
    # DISPLAY ACCOUNT STATE
    # ========================================

    def display_account(self):

        print("\n" + "=" * 60)
        print("AEGIS ACCOUNT")
        print("=" * 60)

        print(
            f"\nCash Balance: "
            f"${self.trader.balance:.2f}"
        )

        print(
            f"Realized P&L: "
            f"${self.trader.realized_pnl:.2f}"
        )

        print("\nOpen Positions")

        if not self.trader.positions:

            print("None")

        else:

            for asset, position in (
                self.trader.positions.items()
            ):

                print(
                    f"{asset}: "
                    f"{position}"
                )

    # ========================================
    # FULL AEGIS STATUS
    # ========================================

    def display_status(self):

        self.display_account()
        self.display_performance()
        self.display_journal()