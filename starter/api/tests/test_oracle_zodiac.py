"""Юнит-тесты оракула zodiac.

Проверяем что для дат, заведомо находящихся внутри знака, оракул возвращает
ожидаемые растения из data/seed/zodiac.json. Стыки знаков сознательно
обходим — там ответ зависит от точного времени.
"""
import json
from pathlib import Path

import pytest

from vlad.models import Person
from vlad.natal.swisseph_wrapper import SIGNS
from vlad.oracles.zodiac import ZodiacOracle


@pytest.fixture
def oracle():
    return ZodiacOracle()


@pytest.mark.parametrize(
    "birth_date, expected_slug",
    [
        ("2000-03-05", "willow"),    # pisces
        ("2000-03-05", "fig"),       # pisces
        ("2000-04-25", "apple"),     # taurus
        ("2000-07-15", "willow"),    # cancer
        ("2000-07-15", "ash"),       # cancer
        ("2000-08-15", "oak"),       # leo
        ("2000-08-15", "cedar"),     # leo
        ("2000-10-05", "maple"),     # libra
        ("2000-10-05", "beech"),     # libra
        ("2000-12-15", "rowan"),     # sagittarius
        ("2000-01-05", "pine"),      # capricorn
    ],
)
def test_known_signs_yield_expected_plants(seeded_session, oracle, birth_date, expected_slug):
    person = Person(first_name="X", birth_date=birth_date)
    results = oracle.run(person, seeded_session)
    slugs = [r.plant_slug for r in results]
    assert expected_slug in slugs, f"{birth_date}: ожидалось {expected_slug}, получено {slugs}"


def test_meta_carries_sun_sign(seeded_session, oracle):
    person = Person(first_name="X", birth_date="2000-04-25")
    results = oracle.run(person, seeded_session)
    assert results
    assert results[0].meta == {"sun_sign": "taurus"}


def test_returns_empty_for_missing_birth_date(db_session, oracle):
    person = Person(first_name="X", birth_date="")
    assert oracle.run(person, db_session) == []


def test_zodiac_seed_uses_only_valid_signs():
    """Все sign'ы в data/seed/zodiac.json должны быть из канонического списка."""
    path = Path("/app/data/seed/zodiac.json")
    rows = json.loads(path.read_text(encoding="utf-8"))
    for row in rows:
        sign = row["matcher"]["sign"]
        assert sign in SIGNS, f"unknown sign in zodiac.json: {sign}"


def test_zodiac_seed_plant_slugs_exist(seeded_session):
    """Каждое растение из zodiac.json должно быть в plants.json."""
    from vlad.models import Plant
    from sqlalchemy import select

    known = {p.slug for p in seeded_session.scalars(select(Plant)).all()}
    rows = json.loads(Path("/app/data/seed/zodiac.json").read_text(encoding="utf-8"))
    for row in rows:
        assert row["plant_slug"] in known, f"unknown plant_slug: {row['plant_slug']}"


def test_registry_includes_zodiac():
    from vlad.oracles import ORACLES

    assert "zodiac" in ORACLES
    assert ORACLES["zodiac"].name_ru.startswith("Знаки зодиака")
