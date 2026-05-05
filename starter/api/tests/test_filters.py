"""Юнит-тесты фильтров эксперта.

Тестируются по отдельности: USDA-зона, sun, soil, дерево-враг, is_weed_like.
В реальном пуле через `recommend(...)` они комбинируются — это покрыто
в `test_intersections.py` и `test_routes_recommend.py`.
"""
import pytest
from sqlalchemy import select

from vlad.core.filters import apply_filters, enemy_tree_slugs
from vlad.models import Oracle, OracleEntry, Person, Plant


def _make_pool(*slugs: str, weight: float = 1.0) -> list[dict]:
    return [
        {
            "plant_slug": slug,
            "plant_name_ru": None,
            "plant_short_story": None,
            "match_count": 1,
            "total_weight": weight,
            "sources": [],
        }
        for slug in slugs
    ]


# ---------- USDA ----------

def test_usda_filter_excludes_too_tender(seeded_session):
    """fig имеет min_zone_usda=7. У Person зона 4 — фигу выкидываем.
    Дата 25.04 — окно ±40 дней (16.03–04.06) не задевает ни fig, ни willow."""
    person = Person(first_name="X", birth_date="2000-04-25", garden_zone_usda=4)
    pool = _make_pool("fig", "willow")  # willow.min_zone_usda=3 — ок
    kept, excluded = apply_filters(pool, person, seeded_session)
    slugs = {e["plant_slug"] for e in kept}
    assert "fig" not in slugs
    assert "willow" in slugs
    assert any("USDA" in x.reason and x.plant_slug == "fig" for x in excluded)


def test_usda_filter_off_when_zone_unset(seeded_session):
    """Если у Person не задана garden_zone_usda — фильтр USDA не работает."""
    person = Person(first_name="X", birth_date="2000-04-25", garden_zone_usda=None)
    pool = _make_pool("fig")
    kept, excluded = apply_filters(pool, person, seeded_session)
    assert {e["plant_slug"] for e in kept} == {"fig"}
    assert excluded == []


# ---------- sun / soil ----------

def test_sun_filter_excludes_mismatch(seeded_session):
    """Создаём временное растение с sun='shade' и проверяем, что для участка
    'sun' оно отфильтруется."""
    seeded_session.add(Plant(slug="shade_plant", name_ru="X", category="herb", sun="shade"))
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-01-01", garden_sun="sun")
    kept, excluded = apply_filters(_make_pool("shade_plant"), person, seeded_session)
    assert kept == []
    assert excluded[0].plant_slug == "shade_plant"
    assert "sun" in excluded[0].reason


def test_sun_compatible_pairs(seeded_session):
    """sun='sun_or_part_shade' совместим и с sun, и с part_shade на участке."""
    seeded_session.add(Plant(slug="versatile", name_ru="X", category="herb", sun="sun_or_part_shade"))
    seeded_session.commit()

    for sun_pref in ("sun", "part_shade"):
        person = Person(first_name="X", birth_date="2000-01-01", garden_sun=sun_pref)
        kept, _ = apply_filters(_make_pool("versatile"), person, seeded_session)
        assert {e["plant_slug"] for e in kept} == {"versatile"}, sun_pref


def test_soil_filter(seeded_session):
    seeded_session.add(Plant(slug="dryholic", name_ru="X", category="herb", soil_moisture="dry"))
    seeded_session.commit()

    wet_garden = Person(first_name="X", birth_date="2000-01-01", garden_soil="wet")
    kept, excluded = apply_filters(_make_pool("dryholic"), wet_garden, seeded_session)
    assert kept == []
    assert "soil" in excluded[0].reason


# ---------- дерево-враг ----------

def test_enemy_tree_slugs_for_march_5(seeded_session):
    """Для 05.03 ±40 дней (≈ 24.01–14.04) врагами должны стать кипарис, тополь,
    кедр, сосна, липа, дуб, орешник, рябина, клён. Ива — наше дерево, не враг."""
    enemies = enemy_tree_slugs("2000-03-05", seeded_session)
    expected = {"cypress", "poplar", "cedar", "pine", "linden", "oak", "hazel", "rowan", "maple"}
    assert enemies == expected
    assert "willow" not in enemies


def test_enemy_filter_drops_oak_for_pisces_eva(seeded_session):
    pool = _make_pool("willow", "oak", "apple")
    person = Person(first_name="Ева", birth_date="2000-03-05")
    kept, excluded = apply_filters(pool, person, seeded_session)
    slugs = {e["plant_slug"] for e in kept}
    assert "willow" in slugs
    assert "apple" in slugs
    assert "oak" not in slugs
    assert any("враг" in x.reason for x in excluded)


def test_enemy_invalid_birth_date_returns_empty(seeded_session):
    """Битый birth_date — фильтр дерева-врага не падает, просто становится no-op."""
    assert enemy_tree_slugs("garbage", seeded_session) == set()


# ---------- is_weed_like ----------

def test_weed_like_lowers_weight_but_keeps_plant(seeded_session):
    seeded_session.add(Plant(slug="weed", name_ru="X", category="herb", is_weed_like=1))
    seeded_session.commit()

    pool = _make_pool("weed", weight=2.0)
    person = Person(first_name="X", birth_date="2000-01-01")
    kept, excluded = apply_filters(pool, person, seeded_session)
    assert len(kept) == 1
    assert kept[0]["plant_slug"] == "weed"
    assert kept[0]["total_weight"] == 1.0  # 2.0 × 0.5
    assert any("weed_like" in n for n in kept[0]["notes"])
    assert excluded == []


# ---------- интеграция: пул пере-сортируется после понижения веса ----------

def test_filtered_pool_resorted(seeded_session):
    """is_weed_like понижает вес, и при равном match_count это меняет порядок."""
    seeded_session.add(Plant(slug="weed", name_ru="X", category="herb", is_weed_like=1))
    seeded_session.add(Plant(slug="not_weed", name_ru="Y", category="herb", is_weed_like=0))
    seeded_session.commit()

    pool = [
        {"plant_slug": "weed",     "plant_name_ru": None, "plant_short_story": None,
         "match_count": 1, "total_weight": 1.0, "sources": []},
        {"plant_slug": "not_weed", "plant_name_ru": None, "plant_short_story": None,
         "match_count": 1, "total_weight": 0.8, "sources": []},
    ]
    person = Person(first_name="X", birth_date="2000-01-01")
    kept, _ = apply_filters(pool, person, seeded_session)
    # weed после фильтра весит 0.5; not_weed остался 0.8 → not_weed первый
    assert [e["plant_slug"] for e in kept] == ["not_weed", "weed"]
