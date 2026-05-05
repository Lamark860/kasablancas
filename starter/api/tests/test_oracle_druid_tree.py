"""Юнит-тесты оракула druid_tree.

Проверяем:
- известные даты → правильное дерево (включая обёрнутый диапазон 23.12–01.01);
- 4 одиночных знака (Дуб, Берёза, Олива, Бук);
- день вне покрытия (21.12) → пусто;
- отсутствие birth_date / битый формат → пусто;
- структура OracleResult: вес, role, reason, meta.
"""
import pytest

from vlad.models import Person
from vlad.oracles.druid_tree import DruidTreeOracle
from vlad.seed import seed_oracle_entries, seed_oracles, seed_plants


@pytest.fixture
def seeded(db_session):
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()
    return db_session


@pytest.fixture
def oracle():
    return DruidTreeOracle()


@pytest.mark.parametrize(
    "birth_date, expected_slug",
    [
        ("2000-03-05", "willow"),     # 1-10 марта — ива (главный пример из roadmap)
        ("1990-09-08", "willow"),     # второй период ивы
        ("1990-03-21", "oak"),        # одиночная дата — дуб
        ("1990-06-24", "birch"),      # одиночная дата — берёза
        ("1990-09-23", "olive"),      # одиночная дата — олива
        ("1990-12-22", "beech"),      # одиночная дата — бук
        ("2000-12-25", "apple"),      # внутри обёрнутого диапазона 23.12–01.01
        ("2001-01-01", "apple"),      # последний день обёрнутого диапазона
        ("1985-07-01", "apple"),      # второй период яблони
    ],
)
def test_known_dates_resolve_to_expected_tree(seeded, oracle, birth_date, expected_slug):
    person = Person(first_name="X", birth_date=birth_date)
    results = oracle.run(person, seeded)
    slugs = [r.plant_slug for r in results]
    assert expected_slug in slugs, f"{birth_date} ожидался {expected_slug}, получено {slugs}"


def test_each_date_resolves_to_exactly_one_tree(seeded, oracle):
    """Кроме непокрытого 21.12, любой день года выдаёт ровно одно дерево."""
    from datetime import date, timedelta

    one_day = timedelta(days=1)
    d = date(2001, 1, 1)  # невисокосный, чтобы не возиться с 29.02
    end = date(2002, 1, 1)
    while d < end:
        bd = d.strftime("%Y-%m-%d")
        person = Person(first_name="X", birth_date=bd)
        results = oracle.run(person, seeded)
        if d.month == 12 and d.day == 21:
            assert results == [], "21.12 в research/02 не покрыт — должна быть пустота"
        else:
            assert len(results) == 1, f"{bd}: ожидалось 1 совпадение, получено {len(results)}"
        d += one_day


def test_missing_birth_date_returns_empty(db_session, oracle):
    person = Person(first_name="X", birth_date="")
    assert oracle.run(person, db_session) == []


def test_malformed_birth_date_returns_empty(db_session, oracle):
    person = Person(first_name="X", birth_date="2000/03/05")  # неправильный разделитель
    assert oracle.run(person, db_session) == []


def test_result_carries_metadata(seeded, oracle):
    person = Person(first_name="X", birth_date="2000-03-05")
    results = oracle.run(person, seeded)
    assert len(results) == 1
    r = results[0]
    assert r.plant_slug == "willow"
    assert r.role == "main"
    assert r.weight == 1.0
    assert "Ива" in r.reason_for_expert
    assert r.reason_for_client.startswith("Ваше дерево — Ива")
    assert r.meta == {"period": "03-01–03-10"}


def test_registry_includes_druid_tree():
    from vlad.oracles import ORACLES

    assert "druid_tree" in ORACLES
    assert ORACLES["druid_tree"].name_ru.startswith("Кельтский")
