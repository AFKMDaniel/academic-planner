from app.database.connection import SessionLocal


def test_database_session():
    session = SessionLocal()
    try:
        assert session is not None
    finally:
        session.close()
