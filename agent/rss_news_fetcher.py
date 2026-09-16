import feedparser


class RSSNewsFetcher:

    def fetch_news(self, symbol: str = "AAPL", limit: int = 5):

        url = (
            "https://feeds.finance.yahoo.com/rss/2.0/headline"
            f"?s={symbol}&region=US&lang=en-US"
        )

        feed = feedparser.parse(url)

        articles = []

        for entry in feed.entries[:limit]:

            articles.append(
                {
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "published": entry.get("published", ""),
                    "summary": entry.get("summary", ""),
                }
            )

        return articles