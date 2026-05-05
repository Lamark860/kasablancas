"""Юнит-тесты оракула name."""
import pytest

from vlad.models import Person
from vlad.oracles.name import NameOracle


@pytest.fixture
def oracle():
    return NameOracle()


def test_iva_resolves_to_willow(seeded_session, oracle):
    person = Person(first_name="Ива", birth_date="2000-01-01")
    results = oracle.run(person, seeded_session)
    assert {r.plant_slug for r in results} == {"willow"}


def test_case_insensitive(seeded_session, oracle):
    for variant in ("ива", "ИВА", "Ива"):
        person = Person(first_name=variant, birth_date="2000-01-01")
        slugs = {r.plant_slug for r in oracle.run(person, seeded_session)}
        assert slugs == {"willow"}, variant


def test_darya_two_plants(seeded_session, oracle):
    person = Person(first_name="Дарья", birth_date="2000-01-01")
    slugs = {r.plant_slug for r in oracle.run(person, seeded_session)}
    assert slugs == {"oak", "ash"}


def test_eva_returns_apple(seeded_session, oracle):
    person = Person(first_name="Ева", birth_date="2000-01-01")
    slugs = {r.plant_slug for r in oracle.run(person, seeded_session)}
    assert slugs == {"apple"}


def test_unknown_name_returns_empty(seeded_session, oracle):
    person = Person(first_name="ИмяКоторогоНетВБазе", birth_date="2000-01-01")
    assert oracle.run(person, seeded_session) == []


def test_meta_carries_normalized_name(seeded_session, oracle):
    person = Person(first_name="ИВА", birth_date="2000-01-01")
    results = oracle.run(person, seeded_session)
    assert results[0].meta == {"name": "ива"}
