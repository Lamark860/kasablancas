"""Проверяем что все ожидаемые таблицы и ключевые колонки описаны в моделях."""
from sqlalchemy import inspect

from vlad.db import Base
import vlad.models  # noqa: F401


EXPECTED_TABLES = {
    "persons",
    "plants",
    "oracles",
    "oracle_entries",
    "recommendations",
    "natal_charts",
}


def test_all_tables_registered():
    actual = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - actual
    assert not missing, f"в Base.metadata не зарегистрированы таблицы: {missing}"


def test_persons_required_columns():
    cols = {c.name for c in Base.metadata.tables["persons"].columns}
    must_have = {
        "id", "first_name", "birth_date",
        "eye_color", "garden_zone_usda", "garden_soil", "garden_sun",
        "created_at", "updated_at",
    }
    assert must_have.issubset(cols)


def test_plants_unique_slug():
    slug = Base.metadata.tables["plants"].columns["slug"]
    assert slug.unique is True
    assert slug.nullable is False


def test_oracle_entry_foreign_keys():
    table = Base.metadata.tables["oracle_entries"]
    fks = {(fk.parent.name, fk.column.table.name, fk.column.name) for fk in table.foreign_keys}
    assert ("oracle_id", "oracles", "id") in fks
    assert ("plant_slug", "plants", "slug") in fks


def test_db_inspectable_after_create_all(db_session):
    """Schema, созданная моделями, инспектируется без ошибок."""
    insp = inspect(db_session.bind)
    tables = set(insp.get_table_names())
    assert EXPECTED_TABLES.issubset(tables)
