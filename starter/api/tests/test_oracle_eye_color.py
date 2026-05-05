"""Юнит-тесты оракула eye_color."""
import pytest

from vlad.models import Person
from vlad.oracles.eye_color import EyeColorOracle


@pytest.fixture
def oracle():
    return EyeColorOracle()


@pytest.mark.parametrize(
    "color, expected",
    [
        ("blue",  {"willow"}),
        ("grey",  {"willow"}),
        ("brown", {"oak", "walnut", "chestnut", "rowan"}),
        ("hazel", {"hazel"}),
        ("amber", {"linden"}),
    ],
)
def test_known_colors(seeded_session, oracle, color, expected):
    person = Person(first_name="X", birth_date="2000-01-01", eye_color=color)
    results = oracle.run(person, seeded_session)
    assert {r.plant_slug for r in results} == expected


def test_uncovered_colors_yield_empty(seeded_session, oracle):
    """green / dark — нет соответствующих растений в наших 22 (см. DECISIONS.md §16)."""
    for color in ("green", "dark"):
        person = Person(first_name="X", birth_date="2000-01-01", eye_color=color)
        assert oracle.run(person, seeded_session) == []


def test_no_eye_color_returns_empty(seeded_session, oracle):
    person = Person(first_name="X", birth_date="2000-01-01", eye_color=None)
    assert oracle.run(person, seeded_session) == []


def test_meta_carries_color(seeded_session, oracle):
    person = Person(first_name="X", birth_date="2000-01-01", eye_color="brown")
    results = oracle.run(person, seeded_session)
    assert all(r.meta == {"eye_color": "brown"} for r in results)
