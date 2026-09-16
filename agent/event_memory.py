import json
import os


class EventMemory:

    FILE_PATH = "data/processed_events.json"

    def __init__(self):
        self.processed_events = set()
        self._load()

    def _load(self):
        if not os.path.exists(self.FILE_PATH):
            return

        try:
            with open(
                self.FILE_PATH,
                "r",
                encoding="utf-8",
            ) as file:
                data = json.load(file)

            self.processed_events = set(data)

        except (
            json.JSONDecodeError,
            OSError,
        ):
            self.processed_events = set()

    def _save(self):
        directory = os.path.dirname(self.FILE_PATH)

        if directory:
            os.makedirs(
                directory,
                exist_ok=True,
            )

        with open(
            self.FILE_PATH,
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                list(self.processed_events),
                file,
                indent=4,
            )

    def is_processed(self, article: dict) -> bool:

        event_id = article.get("url", "").strip()

        if not event_id:
            return False

        return event_id in self.processed_events

    def mark_processed(self, article: dict):

        event_id = article.get("url", "").strip()

        if not event_id:
            return

        self.processed_events.add(event_id)

        self._save()

    def count(self) -> int:
        return len(self.processed_events)

    def reset(self):
        self.processed_events = set()
        self._save()

        print("Event memory reset successfully.")