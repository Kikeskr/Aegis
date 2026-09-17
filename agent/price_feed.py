import yfinance as yf


class PriceFeed:

    def get_price(self, symbol: str) -> float:
        ticker = yf.Ticker(symbol)

        history = ticker.history(
            period="1d",
            interval="1m",
            prepost=True,
            auto_adjust=False,
        )

        if history.empty:
            raise RuntimeError(
                f"No market price available for {symbol}."
            )

        close_prices = history["Close"].dropna()

        if close_prices.empty:
            raise RuntimeError(
                f"No valid market price available for {symbol}."
            )

        price = close_prices.iloc[-1]

        return float(price)