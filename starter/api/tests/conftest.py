"""Pytest-фикстуры.

- `db_session` — чистая SQLite in-memory с накаченной схемой (Base.metadata).
- `seeded_session` — ту же in-memory, но с залитыми сидами (oracles + plants + entries).
- `client` — TestClient для FastAPI с переопределённым get_db, чтобы каждый
  тест работал на своей in-memory БД, а не на общей файловой.
"""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from vlad.db import Base, get_db
import vlad.models  # noqa: F401  — регистрирует все таблицы в Base.metadata


@pytest.fixture
def db_session():
    # StaticPool: одна общая connection между потоками. Без него TestClient
    # (он гоняет хэндлеры в threadpool через anyio) видит пустую in-memory DB
    # в каждом новом потоке, потому что у :memory: каждая connection — свой инстанс.
    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture
def seeded_session(db_session):
    from vlad.seed import seed_oracle_entries, seed_oracles, seed_plants

    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()
    return db_session


@pytest.fixture
def client(db_session):
    """TestClient, привязанный к in-memory db_session через dependency_overrides."""
    from vlad.main import app

    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def seeded_client(seeded_session):
    """Тот же TestClient, но БД уже засеяна."""
    from vlad.main import app

    def _override_get_db():
        yield seeded_session

    app.dependency_overrides[get_db] = _override_get_db
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.pop(get_db, None)
