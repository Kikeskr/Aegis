from agent.events import MarketEvent


class EventFilter:

    def evaluate(self, event: MarketEvent) -> tuple[bool, str]:

        # No identifiable asset = nothing Aegis can trade
        if not event.affected_assets:
            return False, "No affected tradable asset identified."

        # Ignore low-impact events
        if event.impact == "LOW":
            return False, "Event impact is too low for trading."

        # Ignore neutral events
        if event.sentiment == "NEUTRAL":
            return False, "Event sentiment is neutral."

        # Only accept recognized impact levels
        if event.impact not in ["MEDIUM", "HIGH"]:
            return False, "Invalid event impact."

        # Only accept recognized sentiments
        if event.sentiment not in ["POSITIVE", "NEGATIVE"]:
            return False, "Invalid event sentiment."

        return True, "Event passed the trading filter."