"""Юнит-тесты оркестратора.

С этапа 4 активны два оракула: druid_tree и zodiac. Поэтому для 5 марта 2000
пул содержит willow с match_count=2 (пересечение) и fig с match_count=1.
Сортировка `(match_count, total_weight)` начинает работать по-настоящему —
willow выше fig.
"""
from vlad.core.orchestrator import recommend
from vlad.models import Oracle, Person


def test_recommend_returns_willow_for_march_5(seeded_session):
    person = Person(first_name="Анна", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert {"druid_tree", "zodiac"}.issubset(out["active_oracles"])

    pool = out["pool"]
    assert pool[0]["plant_slug"] == "willow"
    assert pool[0]["plant_name_ru"] == "Ива"
    assert pool[0]["match_count"] == 2
    assert pool[0]["total_weight"] == 2.0
    src_oracles = {s["oracle_id"] for s in pool[0]["sources"]}
    assert src_oracles == {"druid_tree", "zodiac"}


def test_recommend_with_missing_birth_date(seeded_session):
    person = Person(first_name="X", birth_date="")
    out = recommend(person, seeded_session)
    assert out["pool"] == []


def test_recommend_skips_inactive_oracle(seeded_session):
    """Выключенный druid_tree не должен голосовать; zodiac остаётся."""
    seeded_session.get(Oracle, "druid_tree").active = 0
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert "druid_tree" not in out["active_oracles"]
    assert "zodiac" in out["active_oracles"]
    sources = {s["oracle_id"] for e in out["pool"] for s in e["sources"]}
    assert sources == {"zodiac"}


def test_recommend_applies_oracle_global_weight(seeded_session):
    """total_weight = сила голоса × глобальный вес оракула.

    Выключаем zodiac, чтобы голосовал один druid_tree, и понижаем его weight
    до 0.5 — итоговый total_weight для willow должен стать 0.5.
    """
    seeded_session.get(Oracle, "zodiac").active = 0
    druid = seeded_session.get(Oracle, "druid_tree")
    druid.weight = 0.5
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert out["pool"][0]["plant_slug"] == "willow"
    assert out["pool"][0]["total_weight"] == 0.5


def test_recommend_includes_short_story(seeded_session):
    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert "Ива" in out["pool"][0]["plant_short_story"]
