"""Tests for db/database.py — engine, session factory, and Base."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.db.database import Base, SessionLocal, engine, get_db


def test_engine_creation() -> None:
    """Engine should be a SQLAlchemy Engine instance."""
    assert engine is not None


def test_session_local() -> None:
    """SessionLocal should be a sessionmaker."""
    assert callable(SessionLocal)


def test_base_declarative() -> None:
    """Base should be a declarative base class."""
    assert hasattr(Base, "metadata")


def test_session_open_close() -> None:
    """A session can be opened and closed without error."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    test_session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = test_session()
    try:
        assert db.is_active
    finally:
        db.close()


def test_get_db_yields_session() -> None:
    """get_db() generator yields a Session and closes it."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    import app.db.database as db_mod

    original_engine = db_mod.engine
    original_session_local = db_mod.SessionLocal
    try:
        db_mod.engine = engine
        db_mod.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        gen = get_db()
        db = next(gen)
        assert isinstance(db, Session)
        assert db.is_active
        with pytest.raises(StopIteration):
            next(gen)
            # After generator exit, calling db methods should raise as session is closed
            from sqlalchemy import text as sql_text
            import sqlalchemy.exc
            with pytest.raises(sqlalchemy.exc.ResourceClosedError):
                db.execute(sql_text("SELECT 1"))
    finally:
        db_mod.engine = original_engine
        db_mod.SessionLocal = original_session_local
