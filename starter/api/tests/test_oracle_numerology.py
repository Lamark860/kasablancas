"""Юнит-тесты оракула numerology (имя по Пифагору)."""
import pytest

from vlad.models import Person
from vlad.oracles.numerology import NumerologyOracle, name_number


@pytest.fixture
def oracle():
    return NumerologyOracle()


@pytest.mark.parametrize(
    "name, expected",
    [
        ("Анна", 5),       # А(1)+Н(6)+Н(6)+А(1)=14 → 1+4=5
        ("Ева",  1),       # Е(6)+В(3)+А(1)=10 → 1
        ("Иван", 2),       # И(1)+В(3)+А(1)+Н(6)=11 → 2
        ("Пётр", 8),       # П(8)+Ё(7)+Т(2)+Р(9)=26 → 8
        ("Лев",  4),       # Л(4)+Е(6)+В(3)=13 → 4
    ],
)
def test_name_number_pythagorean(name, expected):
    assert name_number(name) == expected


def test_name_number_edge_cases():
    assert name_number("") is None
    assert name_number("   ") is None
    assert name_number("123") is None         # цифры не учитываются
    assert name_number("Anna") is None        # латиница не в таблице кириллицы


def test_oracle_returns_birch_and_rowan_for_anna(seeded_session, oracle):
    person = Person(first_name="Анна", birth_date="2000-01-01")
    results = oracle.run(person, seeded_session)
    slugs = {r.plant_slug for r in results}
    assert {"birch", "rowan"} == slugs


def test_oracle_returns_oak_for_eva(seeded_session, oracle):
    person = Person(first_name="Ева", birth_date="2000-01-01")
    results = oracle.run(person, seeded_session)
    assert [r.plant_slug for r in results] == ["oak"]


def test_oracle_meta_carries_name_number(seeded_session, oracle):
    person = Person(first_name="Ева", birth_date="2000-01-01")
    results = oracle.run(person, seeded_session)
    assert results[0].meta == {"name_number": 1}


def test_oracle_empty_name_returns_empty(db_session, oracle):
    person = Person(first_name="", birth_date="2000-01-01")
    assert oracle.run(person, db_session) == []
