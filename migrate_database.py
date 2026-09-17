import sqlite3
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "data" / "aegis.db"


def column_exists(cursor, table_name: str, column_name: str) -> bool:
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    return any(column[1] == column_name for column in columns)


def migrate_database():
    print("=" * 60)
    print("AEGIS DATABASE MIGRATION")
    print("=" * 60)

    if not DATABASE_PATH.exists():
        print(f"Database not found: {DATABASE_PATH}")
        return

    connection = sqlite3.connect(DATABASE_PATH)
    cursor = connection.cursor()

    try:
        # ---------------------------------------------------------
        # PAPER WALLETS
        # ---------------------------------------------------------

        if not column_exists(
            cursor,
            "paper_wallets",
            "initial_balance",
        ):
            print("Adding paper_wallets.initial_balance...")

            cursor.execute(
                """
                ALTER TABLE paper_wallets
                ADD COLUMN initial_balance REAL
                NOT NULL
                DEFAULT 10000.0
                """
            )

            print("Added initial_balance.")

        else:
            print("paper_wallets.initial_balance already exists.")

        # ---------------------------------------------------------
        # TRADES
        # ---------------------------------------------------------

        if not column_exists(
            cursor,
            "trades",
            "return_pct",
        ):
            print("Adding trades.return_pct...")

            cursor.execute(
                """
                ALTER TABLE trades
                ADD COLUMN return_pct REAL
                NOT NULL
                DEFAULT 0.0
                """
            )

            print("Added return_pct.")

        else:
            print("trades.return_pct already exists.")

        connection.commit()

        print()
        print("Migration completed successfully.")

    except Exception as error:
        connection.rollback()
        print()
        print("Migration failed.")
        print(f"Error: {error}")
        raise

    finally:
        connection.close()

    print("=" * 60)


if __name__ == "__main__":
    migrate_database()