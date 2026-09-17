from __future__ import annotations

import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone


class RSSNewsFetcher:
    """
    Multi-source market news ingestion for Aegis.

    Sources:
    - Google News RSS search
    - Yahoo Finance RSS

    The fetcher normalizes articles into the structure expected by
    AegisBackgroundWorker.
    """

    GOOGLE_NEWS_URL = "https://news.google.com/rss/search"

    YAHOO_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"

    DEFAULT_SYMBOLS = [
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
    ]

    SYMBOL_QUERIES = {
        "NVDA": "NVIDIA NVDA stock",
        "AAPL": "Apple AAPL stock",
        "GOOGL": "Alphabet Google GOOGL stock",
        "AMD": "AMD semiconductor stock",
        "TSLA": "Tesla TSLA stock",
        "MSFT": "Microsoft MSFT stock",
        "AMZN": "Amazon AMZN stock",
        "META": "Meta META stock",
        "SPY": "S&P 500 SPY market",
        "QQQ": "Nasdaq QQQ market",
    }

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def fetch_news(
        self,
        symbol: str = "NVDA",
        limit: int = 5,
    ) -> list[dict]:
        """
        Backwards-compatible single-symbol fetch.
        """
        symbol = symbol.upper()

        articles = []

        articles.extend(
            self._fetch_google_news(
                symbol=symbol,
                limit=limit,
            )
        )

        articles.extend(
            self._fetch_yahoo(
                symbol=symbol,
                limit=limit,
            )
        )

        return self._deduplicate_and_sort(articles, limit=limit)

    def fetch_market_news(
        self,
        symbols: list[str] | None = None,
        per_symbol: int = 3,
    ) -> list[dict]:
        """
        Fetch fresh market news across multiple assets.

        This is the main ingestion method used by the autonomous worker.
        """
        symbols = symbols or self.DEFAULT_SYMBOLS

        all_articles = []

        for symbol in symbols:
            try:
                articles = self.fetch_news(
                    symbol=symbol,
                    limit=per_symbol,
                )

                all_articles.extend(articles)

                print(
                    f"[NEWS] {symbol}: "
                    f"{len(articles)} article(s)"
                )

            except Exception as error:
                print(
                    f"[NEWS] {symbol} fetch failed: {error}"
                )

        return self._deduplicate_and_sort(
            all_articles,
            limit=None,
        )

    def _fetch_google_news(
        self,
        symbol: str,
        limit: int,
    ) -> list[dict]:
        query = self.SYMBOL_QUERIES.get(
            symbol,
            f"{symbol} stock market",
        )

        params = urllib.parse.urlencode(
            {
                "q": query,
                "hl": "en-US",
                "gl": "US",
                "ceid": "US:en",
            }
        )

        url = f"{self.GOOGLE_NEWS_URL}?{params}"

        root = self._fetch_xml(url)

        articles = []

        for item in root.findall(".//item")[:limit]:
            title = self._clean_text(
                item.findtext("title", "")
            )

            link = self._clean_text(
                item.findtext("link", "")
            )

            description = self._clean_text(
                item.findtext("description", "")
            )

            pub_date = self._clean_text(
                item.findtext("pubDate", "")
            )

            source_node = item.find("source")

            source = (
                source_node.text.strip()
                if source_node is not None
                and source_node.text
                else "Google News"
            )

            if not title or not link:
                continue

            articles.append(
                {
                    "title": title,
                    "summary": description,
                    "url": link,
                    "published_at": pub_date,
                    "source": source,
                    "symbol": symbol,
                }
            )

        return articles

    def _fetch_yahoo(
        self,
        symbol: str,
        limit: int,
    ) -> list[dict]:
        params = urllib.parse.urlencode(
            {
                "s": symbol,
                "region": "US",
                "lang": "en-US",
            }
        )

        url = f"{self.YAHOO_URL}?{params}"

        root = self._fetch_xml(url)

        articles = []

        for item in root.findall(".//item")[:limit]:
            title = self._clean_text(
                item.findtext("title", "")
            )

            link = self._clean_text(
                item.findtext("link", "")
            )

            description = self._clean_text(
                item.findtext("description", "")
            )

            pub_date = self._clean_text(
                item.findtext("pubDate", "")
            )

            if not title or not link:
                continue

            articles.append(
                {
                    "title": title,
                    "summary": description,
                    "url": link,
                    "published_at": pub_date,
                    "source": "Yahoo Finance",
                    "symbol": symbol,
                }
            )

        return articles

    def _fetch_xml(self, url: str) -> ET.Element:
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/130 Safari/537.36"
                )
            },
        )

        with urllib.request.urlopen(
            request,
            timeout=self.timeout,
        ) as response:
            data = response.read()

        return ET.fromstring(data)

    @staticmethod
    def _deduplicate_and_sort(
        articles: list[dict],
        limit: int | None = None,
    ) -> list[dict]:
        seen_urls = set()
        seen_titles = set()
        unique = []

        for article in articles:
            url = article.get("url", "").strip()
            title = article.get("title", "").strip()

            normalized_title = re.sub(
                r"\s+",
                " ",
                title.lower(),
            )

            if url and url in seen_urls:
                continue

            if normalized_title and normalized_title in seen_titles:
                continue

            if url:
                seen_urls.add(url)

            if normalized_title:
                seen_titles.add(normalized_title)

            unique.append(article)

        unique.sort(
            key=RSSNewsFetcher._article_sort_key,
            reverse=True,
        )

        if limit is not None:
            return unique[:limit]

        return unique

    @staticmethod
    def _article_sort_key(article: dict):
        value = article.get("published_at", "")

        if not value:
            return datetime.min.replace(
                tzinfo=timezone.utc
            )

        try:
            from email.utils import parsedate_to_datetime

            parsed = parsedate_to_datetime(value)

            if parsed.tzinfo is None:
                parsed = parsed.replace(
                    tzinfo=timezone.utc
                )

            return parsed
        except Exception:
            return datetime.min.replace(
                tzinfo=timezone.utc
            )

    @staticmethod
    def _clean_text(value: str | None) -> str:
        if not value:
            return ""

        value = re.sub(
            r"<[^>]+>",
            " ",
            value,
        )

        value = value.replace(
            "&nbsp;",
            " ",
        )

        value = value.replace(
            "&amp;",
            "&",
        )

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()


if __name__ == "__main__":
    fetcher = RSSNewsFetcher()

    print("=" * 70)
    print("AEGIS MULTI-SOURCE NEWS TEST")
    print("=" * 70)

    articles = fetcher.fetch_market_news(
        symbols=[
            "NVDA",
            "AAPL",
            "GOOGL",
            "AMD",
            "TSLA",
        ],
        per_symbol=3,
    )

    print(
        f"\nTotal unique articles: {len(articles)}\n"
    )

    for index, article in enumerate(
        articles,
        start=1,
    ):
        print("-" * 70)
        print(f"{index}. {article['title']}")
        print(f"Source: {article['source']}")
        print(f"Symbol: {article['symbol']}")
        print(f"URL: {article['url']}")