"""Тесты обёртки над swisseph и кеширования натальной карты.

Sun sign — самый стабильный параметр, определяется просто по дате (плюс-минус
сутки). Проверяем несколько хорошо изученных дат вдали от стыков знаков.
"""
from datetime import date, time

import pytest

from vlad.models import NatalChart, Person
from vlad.natal.cache import get_or_calc_chart
from vlad.natal.swisseph_wrapper import (
    SIGNS,
    calc_chart,
    parse_birth_date,
    parse_birth_time,
)


@pytest.mark.parametrize(
    "birth_date, expected_sun",
    [
        (date(2000, 3, 5),  "pisces"),       # 5 марта — глубоко в Рыбах
        (date(2000, 4, 25), "taurus"),       # 25 апреля — Телец
        (date(2000, 7, 15), "cancer"),       # 15 июля — Рак
        (date(2000, 10, 5), "libra"),        # 5 октября — Весы
        (date(2000, 1, 5),  "capricorn"),    # 5 января — Козерог
    ],
)
def test_calc_chart_sun_sign(birth_date, expected_sun):
    chart = calc_chart(birth_date)
    assert chart.sun_sign == expected_sun
    assert chart.moon_sign in SIGNS
    assert chart.ascendant_sign is None  # без времени асцендента быть не может


def test_calc_chart_element_counts_sum_to_planet_count():
    chart = calc_chart(date(2000, 3, 5))
    total = chart.fire_count + chart.earth_count + chart.air_count + chart.water_count
    assert total == 10  # 10 планет в PLANETS


def test_calc_chart_with_time_and_coords_yields_ascendant():
    """Москва, 12:00 местного — асцендент должен посчитаться."""
    chart = calc_chart(
        birth_date=date(2000, 7, 15),
        birth_time=time(12, 0),
        lat=55.75,
        lon=37.62,
        tz="Europe/Moscow",
    )
    assert chart.ascendant_sign in SIGNS


def test_parse_helpers():
    assert parse_birth_date("2000-03-05") == date(2000, 3, 5)
    assert parse_birth_date("") is None
    assert parse_birth_date("garbage") is None
    assert parse_birth_time("12:30") == time(12, 30)
    assert parse_birth_time("") is None
    assert parse_birth_time(None) is None


def test_get_or_calc_chart_returns_none_without_birth_date(db_session):
    person = Person(first_name="X", birth_date="")
    assert get_or_calc_chart(person, db_session) is None


def test_get_or_calc_chart_inline_person_no_caching(db_session):
    """Эфемерный Person (без id) — карта считается, но не сохраняется."""
    person = Person(first_name="X", birth_date="2000-03-05")
    chart = get_or_calc_chart(person, db_session)
    assert chart is not None
    assert chart.sun_sign == "pisces"
    assert db_session.query(NatalChart).count() == 0


def test_get_or_calc_chart_caches_for_saved_person(db_session):
    person = Person(first_name="X", birth_date="2000-03-05")
    db_session.add(person)
    db_session.commit()

    chart1 = get_or_calc_chart(person, db_session)
    assert chart1 is not None
    assert db_session.query(NatalChart).count() == 1

    # повторный вызов — берёт из кеша, не пишет ещё одну строку
    chart2 = get_or_calc_chart(person, db_session)
    assert chart2.sun_sign == chart1.sun_sign
    assert db_session.query(NatalChart).count() == 1
