from datetime import datetime, timezone

from sqlalchemy import DateTime, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

from api.database import DATABASE_URL


class EventMemoryBase(DeclarativeBase):
    pass


class ProcessedEvent(EventMemoryBase):
    __tablename__ = "processed_events_db"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    event_key: Mapped[str] = mapped_column(
        String(500),
        unique=True,
        index=True,
        nullable=False,
    )

    title: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    url: Mapped[str] = mapped_column(
        String(1000),
        default="",
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False,
    },
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


EventMemoryBase.metadata.create_all(
    bind=engine,
)


class DatabaseEventMemory:

    def __init__(self):
        self.db = SessionLocal()

    # ========================================================
    # EVENT KEY
    # ========================================================

    @staticmethod
    def event_key(article: dict) -> str:

        url = (
            article.get(
                "url",
                "",
            )
            .strip()
        )

        if url:
            return url

        title = (
            article.get(
                "title",
                "",
            )
            .strip()
            .lower()
        )

        return title

    # ========================================================
    # CHECK
    # ========================================================

    def is_processed(
        self,
        article: dict,
    ) -> bool:

        key = self.event_key(article)

        if not key:
            return False

        return (
            self.db.query(
                ProcessedEvent
            )
            .filter(
                ProcessedEvent.event_key
                == key
            )
            .first()
            is not None
        )

    # ========================================================
    # MARK PROCESSED
    # ========================================================

    def mark_processed(
        self,
        article: dict,
    ) -> None:

        key = self.event_key(article)

        if not key:
            return

        existing = (
            self.db.query(
                ProcessedEvent
            )
            .filter(
                ProcessedEvent.event_key
                == key
            )
            .first()
        )

        if existing:
            return

        record = ProcessedEvent(
            event_key=key,
            title=article.get(
                "title",
                "",
            ),
            url=article.get(
                "url",
                "",
            ),
        )

        self.db.add(record)
        self.db.commit()

    # ========================================================
    # CLOSE
    # ========================================================

    def close(self):

        self.db.close()