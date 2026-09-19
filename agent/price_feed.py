import time
from threading import Lock

import yfinance as yf


class PriceFeed:
    """
    Centralized market price feed for Aegis.

    Uses Yahoo Finance through yfinance.

    Features:
        - Latest available market price
        - Extended-hours support
        - Short in-memory cache to avoid duplicate requests
        - Thread-safe access
        - Fast-price lookup with history fallback
    """

    CACHE_SECONDS = 2.0

    def __init__(self):
        self._cache = {}
        self._lock = Lock()

    # ========================================================
    # PUBLIC PRICE API
    # ========================================================

    def get_price(self, symbol: str) -> float:

        symbol = symbol.upper().strip()

        if not symbol:
            raise ValueError(
                "Symbol cannot be empty."
            )

        now = time.monotonic()

        # ----------------------------------------------------
        # SHORT CACHE
        # ----------------------------------------------------

        with self._lock:

            cached = self._cache.get(symbol)

            if cached:

                cached_price, cached_time = cached

                if (
                    now - cached_time
                    < self.CACHE_SECONDS
                ):
                    return cached_price

        # ----------------------------------------------------
        # FETCH CURRENT PRICE
        # ----------------------------------------------------

        price = self._fetch_price(symbol)

        # ----------------------------------------------------
        # STORE CACHE
        # ----------------------------------------------------

        with self._lock:

            self._cache[symbol] = (
                price,
                now,
            )

        return price

    # ========================================================
    # PRICE FETCH
    # ========================================================

    @staticmethod
    def _fetch_price(symbol: str) -> float:

        ticker = yf.Ticker(symbol)

        # ----------------------------------------------------
        # FIRST ATTEMPT:
        # yfinance fast_info
        # ----------------------------------------------------

        try:

            fast_info = ticker.fast_info

            last_price = fast_info.get(
                "lastPrice"
            )

            if last_price is not None:

                price = float(last_price)

                if price > 0:

                    return price

        except Exception:
            pass

        # ----------------------------------------------------
        # FALLBACK:
        # 1-MINUTE MARKET DATA
        # ----------------------------------------------------

        try:

            history = ticker.history(
                period="1d",
                interval="1m",
                prepost=True,
                auto_adjust=False,
            )

        except Exception as error:

            raise RuntimeError(
                f"Unable to retrieve current "
                f"price for {symbol}: {error}"
            ) from error

        if history.empty:

            raise RuntimeError(
                f"No market price available "
                f"for {symbol}."
            )

        close_prices = (
            history["Close"]
            .dropna()
        )

        if close_prices.empty:

            raise RuntimeError(
                f"No valid market price "
                f"available for {symbol}."
            )

        price = float(
            close_prices.iloc[-1]
        )

        if price <= 0:

            raise RuntimeError(
                f"Invalid market price "
                f"received for {symbol}."
            )

        return price

    # ========================================================
    # CACHE MANAGEMENT
    # ========================================================

    def clear(self, symbol: str | None = None):

        with self._lock:

            if symbol is None:

                self._cache.clear()

                return

            self._cache.pop(
                symbol.upper().strip(),
                None,
            )

    # ========================================================
    # DEBUG / STATUS
    # ========================================================

    def get_cached_price(
        self,
        symbol: str,
    ) -> float | None:

        symbol = symbol.upper().strip()

        with self._lock:

            cached = self._cache.get(symbol)

            if not cached:
                return None

            return cached[0]