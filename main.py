import time

from agent.event_loop import EventLoop
from agent.rss_news_fetcher import RSSNewsFetcher


# --------------------------------
# AEGIS CONFIGURATION
# --------------------------------

NEWS_INTERVAL = 60  # seconds between news scans


# --------------------------------
# INITIALIZE AEGIS
# --------------------------------

aegis = EventLoop()
news_fetcher = RSSNewsFetcher()


# --------------------------------
# DISPLAY STARTUP
# --------------------------------

print("\n" + "=" * 60)
print("AEGIS AUTONOMOUS EVENT-DRIVEN AGENT")
print("=" * 60)

print("\nAegis is now running continuously.")
print(f"News scan interval: {NEWS_INTERVAL} seconds")
print("Press CTRL+C to stop Aegis.")


# --------------------------------
# AUTONOMOUS LOOP
# --------------------------------

try:

    while True:

        print("\n" + "=" * 60)
        print("AEGIS MARKET SCAN")
        print("=" * 60)

        print("\nFetching latest market news...")

        try:

            articles = news_fetcher.fetch_news(
                limit=5,
            )

            print(
                f"Found {len(articles)} news articles."
            )

        except Exception as error:

            print("\nNEWS FETCH ERROR")
            print(error)

            articles = []


        # --------------------------------
        # PROCESS NEWS EVENTS
        # --------------------------------

        for article in articles:

            try:

                aegis.process_article(
                    article=article,
                )

            except Exception as error:

                print("\nERROR PROCESSING ARTICLE")
                print(error)


        # --------------------------------
        # MONITOR OPEN POSITIONS
        # --------------------------------

        aegis.monitor_positions()


        # --------------------------------
        # DISPLAY PERFORMANCE
        # --------------------------------

        aegis.display_performance()


        # --------------------------------
        # DISPLAY ACCOUNT
        # --------------------------------

        aegis.display_account()


        # --------------------------------
        # WAIT FOR NEXT SCAN
        # --------------------------------

        print("\n" + "=" * 60)
        print("AEGIS WAITING")
        print("=" * 60)

        print(
            f"\nNext market scan in "
            f"{NEWS_INTERVAL} seconds..."
        )

        time.sleep(NEWS_INTERVAL)


# --------------------------------
# GRACEFUL SHUTDOWN
# --------------------------------

except KeyboardInterrupt:

    print("\n\n" + "=" * 60)
    print("AEGIS SHUTDOWN")
    print("=" * 60)

    print("\nFinal account state:")
    aegis.display_account()

    print("\nFinal performance:")
    aegis.display_performance()

    print("\nAegis stopped safely.")