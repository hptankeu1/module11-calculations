"""Shared fixtures.

Integration tests talk to a real PostgreSQL database (the service container in
GitHub Actions, or a local Postgres / docker compose locally). Each test runs
inside a transaction that is rolled back afterwards, so tests are isolated and
the database stays clean.
"""
import os

import pytest

# Point the app at the test database *before* app.database is imported.
os.environ.setdefault(
    "DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/calc_test"
)

from sqlalchemy.orm import Session  # noqa: E402

from app.database import Base, engine  # noqa: E402
from app.models import User  # noqa: E402
from app.security import hash_password  # noqa: E402


@pytest.fixture(scope="session")
def db_engine():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db_session(db_engine):
    """A session bound to an outer transaction that is always rolled back.

    ``join_transaction_mode="create_savepoint"`` lets code under test call
    ``session.commit()`` freely while everything is still undone at the end.
    """
    connection = db_engine.connect()
    outer = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint", expire_on_commit=False)
    try:
        yield session
    finally:
        session.close()
        outer.rollback()
        connection.close()


@pytest.fixture()
def user(db_session) -> User:
    u = User(username="alice", email="alice@example.com", password_hash=hash_password("Secret123"))
    db_session.add(u)
    db_session.commit()
    return u
