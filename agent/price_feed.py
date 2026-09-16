import yfinance as yf


class PriceFeed:

    def get_price(self, symbol: str) -> float:

        ticker = yf.Ticker(symbol)

        history = ticker.history(
            period="1d",
            interval="1m",
        )

        if history.empty:
            raise RuntimeError(
                f"No market price available for {symbol}."
            )

        price = history["Close"].dropna().iloc[-1]

        return float(price)