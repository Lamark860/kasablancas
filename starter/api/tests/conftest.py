"""Pytest-фикстуры.

Главная — `db_session`: чистая SQLite in-memory для каждого теста, со всеми
таблицами, созданными по текущим ORM-моделям (без alembic). Это даёт изоляцию
и быстрый прогон, при этом структуру БД проверяет отдельный тест на миграции
(см. test_schema.py).
"""
from __future__ import annotations

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from vlad.db import Base
import vlad.models  # noqa: F401  — регистрирует все таблицы в Base.metadata


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", future=True)
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
