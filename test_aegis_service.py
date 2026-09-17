from agent.events import MarketEvent
from api.database import Base, SessionLocal, engine
from api.models import PaperWallet, User
from api.aegis_service import AegisService


def run_test():

    Base.metadata.create_all(
        bind=engine
    )

    db = SessionLocal()

    user = None
    wallet = None

    try:

        # -------------------------------------------------
        # CREATE TEST USER
        # -------------------------------------------------

        user = User(
            username="aegis_service_test",
            email="aegis_service_test@example.com",
            password_hash="test_hash",
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        # -------------------------------------------------
        # CREATE PAPER WALLET
        # -------------------------------------------------

        wallet = PaperWallet(
            user_id=user.id,
            balance=10_000.0,
            realized_pnl=0.0,
        )

        db.add(wallet)
        db.commit()
        db.refresh(wallet)

        # -------------------------------------------------
        # CREATE AEGIS SERVICE
        # -------------------------------------------------

        aegis = AegisService(
            db=db,
            wallet=wallet,
        )

        # -------------------------------------------------
        # CREATE TEST EVENT
        # -------------------------------------------------

        event = MarketEvent(
            event_type="PRODUCT",
            description=(
                "NVIDIA announces a major new "
                "AI infrastructure partnership."
            ),
            sentiment="POSITIVE",
            impact="HIGH",
            affected_assets=["NVDA"],
        )

        # -------------------------------------------------
        # PROCESS EVENT
        # -------------------------------------------------

        result = aegis.process_event(
            event=event,
        )

        print("\n" + "=" * 60)
        print("AEGIS SERVICE TEST")
        print("=" * 60)

        print("\nEVENT")
        print(result["event"])

        print("\nFILTER")
        print(result["filter"])

        print("\nQWEN DECISION")
        print(result["decision"])

        print("\nRISK")
        print(result["risk"])

        print("\nEXECUTION")
        print(result["execution"])

        if result.get("portfolio"):
            print("\nPORTFOLIO")
            print(result["portfolio"])

        print("\nPOSITIONS")
        print(aegis.get_positions())

        print("\n" + "=" * 60)
        print("AEGIS SERVICE TEST PASSED")
        print("=" * 60)

    finally:

        if wallet is not None:
            db.delete(wallet)

        if user is not None:
            db.delete(user)

        db.commit()
        db.close()


if __name__ == "__main__":
    run_test()