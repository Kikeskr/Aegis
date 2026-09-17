import time
import threading
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from api import models
from api.aegis_service import AegisService
from api.database import SessionLocal

from agent.database_event_memory import DatabaseEventMemory
from agent.qwen_agent import classify_news
from agent.rss_news_fetcher import RSSNewsFetcher


class AegisBackgroundWorker:
    MAX_OPEN_TRADES = 5

    def __init__(self, interval=60):
        self.interval = interval
        self.running = False
        self.thread = None

        self.news_fetcher = RSSNewsFetcher()
        self.event_memory = DatabaseEventMemory()

        # ========================================================
        # AUTONOMOUS ENGINE STATUS
        # ========================================================

        self.started_at = None
        self.last_cycle_at = None
        self.last_cycle_duration = None

        self.cycles_completed = 0

        self.articles_fetched = 0
        self.new_events = 0
        self.events_rejected = 0
        self.ai_decisions = 0
        self.trades_executed = 0
        self.exits_triggered = 0

        self.last_event_title = None
        self.last_event_time = None

        self.last_error = None

        self._stats_lock = threading.Lock()

    # ============================================================
    # START
    # ============================================================

    def start(self):
        if self.running:
            return

        self.running = True
        self.started_at = self._now()

        self.thread = threading.Thread(
            target=self._run,
            daemon=True,
        )

        self.thread.start()

        print("[AEGIS WORKER] Started.")

    # ============================================================
    # STOP
    # ============================================================

    def stop(self):
        self.running = False

        if self.thread:
            self.thread.join(timeout=2)

        self.event_memory.close()

        print("[AEGIS WORKER] Stopped.")

    # ============================================================
    # MAIN LOOP
    # ============================================================

    def _run(self):
        while self.running:

            try:
                self.process_cycle()

            except Exception as error:

                self.last_error = str(error)

                print(
                    f"[AEGIS WORKER] Cycle error: {error}"
                )

            time.sleep(self.interval)

    # ============================================================
    # AUTONOMOUS CYCLE
    # ============================================================

    def process_cycle(self):

        cycle_started = time.time()
        cycle_time = self._now()

        print("\n" + "=" * 70)
        print("AEGIS AUTONOMOUS EVENT CYCLE")
        print(cycle_time)
        print("=" * 70)

        db = SessionLocal()

        try:

            # ----------------------------------------------------
            # 1. MONITOR EXISTING POSITIONS
            # ----------------------------------------------------

            self.monitor_all_users(db)

            # ----------------------------------------------------
            # 2. GET USERS
            # ----------------------------------------------------

            users = (
                db.query(models.User)
                .all()
            )

            if not users:

                print(
                    "[AEGIS WORKER] No registered users."
                )

                return

            # ----------------------------------------------------
            # 3. CHECK TRADE CAPACITY
            # ----------------------------------------------------

            if not self.has_trade_capacity(
                db=db,
                users=users,
            ):

                print(
                    "[AEGIS WORKER] Maximum of "
                    f"{self.MAX_OPEN_TRADES} open trades reached."
                )

                print(
                    "[AEGIS WORKER] News sourcing paused."
                )

                return

            # ----------------------------------------------------
            # 4. FETCH MARKET NEWS
            # ----------------------------------------------------

            articles = (
                self.news_fetcher.fetch_market_news(
                    symbols=[
                        "NVDA",
                        "AAPL",
                        "GOOGL",
                        "AMD",
                        "TSLA",
                        "MSFT",
                        "AMZN",
                        "META",
                        "SPY",
                        "QQQ",
                    ],
                    per_symbol=3,
                )
            )

            article_count = len(articles or [])

            with self._stats_lock:
                self.articles_fetched += article_count

            if not articles:

                print(
                    "[AEGIS WORKER] No articles returned."
                )

                return

            print(
                f"[AEGIS WORKER] Fetched "
                f"{len(articles)} unique market articles."
            )

            # ----------------------------------------------------
            # 5. PROCESS NEW EVENTS
            # ----------------------------------------------------

            for article in articles:

                # Stop processing new information once all
                # available trade capacity has been consumed.
                if not self.has_trade_capacity(
                    db=db,
                    users=users,
                ):

                    print(
                        "[AEGIS WORKER] Maximum of "
                        f"{self.MAX_OPEN_TRADES} open trades reached."
                    )

                    print(
                        "[AEGIS WORKER] Stopping event sourcing "
                        "for this cycle."
                    )

                    break

                if self.event_memory.is_processed(
                    article
                ):

                    print(
                        "[EVENT MEMORY] Already processed: "
                        f"{article.get('title', '')}"
                    )

                    continue

                with self._stats_lock:
                    self.new_events += 1

                self.process_new_event(
                    db=db,
                    users=users,
                    article=article,
                )

                self.event_memory.mark_processed(
                    article
                )

            # ----------------------------------------------------
            # CYCLE COMPLETE
            # ----------------------------------------------------

            db.commit()

        finally:

            db.close()

            duration = time.time() - cycle_started

            with self._stats_lock:

                self.last_cycle_at = cycle_time
                self.last_cycle_duration = round(
                    duration,
                    3,
                )

                self.cycles_completed += 1

    # ============================================================
    # TRADE CAPACITY
    # ============================================================

    def has_trade_capacity(
        self,
        db: Session,
        users: list,
    ) -> bool:
        """
        Returns True if at least one user has fewer than
        MAX_OPEN_TRADES open positions.

        Aegis stops sourcing new market information when
        all user wallets have reached the maximum.
        """

        for user in users:

            wallet = (
                db.query(models.PaperWallet)
                .filter(
                    models.PaperWallet.user_id
                    == user.id
                )
                .first()
            )

            if not wallet:
                continue

            service = AegisService(
                db=db,
                wallet=wallet,
            )

            positions = service.get_positions()

            open_trades = len(positions)

            if open_trades < self.MAX_OPEN_TRADES:
                return True

        return False

    # ============================================================
    # POSITION MONITORING
    # ============================================================

    def monitor_all_users(
        self,
        db: Session,
    ):

        users = (
            db.query(models.User)
            .all()
        )

        if not users:
            return

        print("\n" + "-" * 70)
        print("AEGIS POSITION MONITOR")
        print("-" * 70)

        total_positions = 0
        total_exits = 0

        for user in users:

            wallet = (
                db.query(models.PaperWallet)
                .filter(
                    models.PaperWallet.user_id
                    == user.id
                )
                .first()
            )

            if not wallet:

                print(
                    f"[USER {user.username}] "
                    "No wallet found."
                )

                continue

            try:

                service = AegisService(
                    db=db,
                    wallet=wallet,
                )

                positions = (
                    service.get_positions()
                )

                if not positions:

                    print(
                        f"[USER {user.username}] "
                        "No open positions."
                    )

                    continue

                total_positions += len(
                    positions
                )

                print(
                    f"[USER {user.username}] "
                    f"Checking {len(positions)} "
                    "open position(s)..."
                )

                results = (
                    service.monitor_positions()
                )

                for result in results:

                    asset = result["asset"]
                    price = result["price"]
                    triggered = result[
                        "exit_triggered"
                    ]
                    message = result["message"]

                    if triggered:

                        total_exits += 1

                        with self._stats_lock:
                            self.exits_triggered += 1

                        print(
                            f"[EXIT] {user.username} | "
                            f"{asset} | "
                            f"${price:.2f}"
                        )

                        print(
                            f"[EXIT] {message}"
                        )

                    else:

                        print(
                            f"[MONITOR] "
                            f"{user.username} | "
                            f"{asset} | "
                            f"${price:.2f} | "
                            "No exit trigger."
                        )

            except Exception as error:

                print(
                    f"[POSITION MONITOR ERROR] "
                    f"{user.username}: {error}"
                )

        print("-" * 70)

        print(
            f"[AEGIS POSITION MONITOR] "
            f"Positions checked: {total_positions}"
        )

        print(
            f"[AEGIS POSITION MONITOR] "
            f"Exits triggered: {total_exits}"
        )

        print("-" * 70)

        db.commit()

    # ============================================================
    # NEW MARKET EVENT
    # ============================================================

    def process_new_event(
        self,
        db: Session,
        users: list,
        article: dict,
    ):

        title = (
            article.get("title", "")
            .strip()
        )

        summary = (
            article.get("summary", "")
            .strip()
        )

        self.last_event_title = title
        self.last_event_time = self._now()

        print("\n" + "-" * 70)
        print("NEW MARKET EVENT")
        print(title)
        print("-" * 70)

        # --------------------------------------------------------
        # QWEN EVENT CLASSIFICATION
        # --------------------------------------------------------

        event = classify_news(
            title=title,
            summary=summary,
        )

        print(
            "[EVENT CLASSIFICATION]"
        )

        print(
            event.model_dump()
        )

        # --------------------------------------------------------
        # PROCESS EVENT FOR EVERY USER
        # --------------------------------------------------------

        for user in users:

            wallet = (
                db.query(models.PaperWallet)
                .filter(
                    models.PaperWallet.user_id
                    == user.id
                )
                .first()
            )

            if not wallet:

                print(
                    f"[USER {user.username}] "
                    "No wallet found."
                )

                continue

            # ----------------------------------------------------
            # PER-USER TRADE LIMIT
            # ----------------------------------------------------

            service = AegisService(
                db=db,
                wallet=wallet,
            )

            current_positions = (
                service.get_positions()
            )

            if len(current_positions) >= self.MAX_OPEN_TRADES:

                print(
                    f"[USER {user.username}] "
                    f"Maximum of {self.MAX_OPEN_TRADES} "
                    "open trades reached. "
                    "Skipping new event execution."
                )

                continue

            print(
                "\n" + ">" * 20
            )

            print(
                f"USER: {user.username}"
            )

            print(
                f"WALLET: {wallet.id}"
            )

            print(
                ">" * 20
            )

            try:

                result = (
                    service.process_event(
                        event
                    )
                )

                self.record_event_statistics(
                    result
                )

                self.print_result(
                    user,
                    result,
                )

            except Exception as error:

                print(
                    f"[USER {user.username}] "
                    f"Processing failed: {error}"
                )

        db.commit()

    # ============================================================
    # EVENT STATISTICS
    # ============================================================

    def record_event_statistics(
        self,
        result: dict,
    ):

        filter_result = (
            result.get("filter")
            or {}
        )

        decision = (
            result.get("decision")
        )

        execution = (
            result.get("execution")
            or {}
        )

        # --------------------------------------------------------
        # FILTER
        # --------------------------------------------------------

        if not filter_result.get(
            "approved",
            False,
        ):

            with self._stats_lock:
                self.events_rejected += 1

        # --------------------------------------------------------
        # AI DECISION
        # --------------------------------------------------------

        if decision is not None:

            with self._stats_lock:
                self.ai_decisions += 1

        # --------------------------------------------------------
        # TRADE
        # --------------------------------------------------------

        if execution.get(
            "executed",
            False,
        ):

            with self._stats_lock:
                self.trades_executed += 1

    # ============================================================
    # EVENT RESULT
    # ============================================================

    @staticmethod
    def print_result(
        user,
        result: dict,
    ):

        print(
            f"\n[{user.username}] EVENT RESULT"
        )

        print(
            f"Filter: "
            f"{result.get('filter')}"
        )

        print(
            f"Decision: "
            f"{result.get('decision')}"
        )

        print(
            f"Risk: "
            f"{result.get('risk')}"
        )

        print(
            f"Execution: "
            f"{result.get('execution')}"
        )

        if result.get("portfolio"):

            print(
                f"Portfolio: "
                f"{result.get('portfolio')}"
            )

    # ============================================================
    # RUN ONCE
    # ============================================================

    def run_once(self):
        self.process_cycle()

    # ============================================================
    # STATUS
    # ============================================================

    def get_status(self) -> dict:

        with self._stats_lock:

            return {
                "running": self.running,
                "interval_seconds": self.interval,

                "started_at": self.started_at,
                "last_cycle_at": self.last_cycle_at,
                "last_cycle_duration": (
                    self.last_cycle_duration
                ),

                "next_cycle_in_seconds": (
                    self._next_cycle_seconds()
                ),

                "cycles_completed": (
                    self.cycles_completed
                ),

                "articles_fetched": (
                    self.articles_fetched
                ),

                "new_events": (
                    self.new_events
                ),

                "events_rejected": (
                    self.events_rejected
                ),

                "ai_decisions": (
                    self.ai_decisions
                ),

                "trades_executed": (
                    self.trades_executed
                ),

                "exits_triggered": (
                    self.exits_triggered
                ),

                "last_event_title": (
                    self.last_event_title
                ),

                "last_event_time": (
                    self.last_event_time
                ),

                "last_error": (
                    self.last_error
                ),

                "mode": "autonomous",
                "max_open_trades": self.MAX_OPEN_TRADES,
            }

    # ============================================================
    # TIME HELPERS
    # ============================================================

    @staticmethod
    def _now():

        return datetime.now(
            timezone.utc
        ).isoformat()

    def _next_cycle_seconds(self):

        if not self.last_cycle_at:
            return self.interval

        try:

            last = datetime.fromisoformat(
                self.last_cycle_at
            )

            elapsed = (
                datetime.now(timezone.utc)
                - last
            ).total_seconds()

            remaining = (
                self.interval - elapsed
            )

            return max(
                0,
                int(remaining),
            )

        except Exception:

            return self.interval


# ================================================================
# DIRECT EXECUTION
# ================================================================

if __name__ == "__main__":

    worker = AegisBackgroundWorker(
        interval=60
    )

    try:

        worker.run_once()

    finally:

        worker.stop()