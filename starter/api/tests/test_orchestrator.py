"""Юнит-тесты оркестратора.

Сейчас активен один оракул (druid_tree), поэтому пул ровно из одного элемента.
Когда подключим остальные на этапе 5, появятся пересечения и сортировка по
match_count начнёт работать «по-настоящему» — отдельный тест на это добавим
тогда.
"""
from vlad.core.orchestrator import recommend
from vlad.models import Oracle, Person


def test_recommend_returns_willow_for_march_5(seeded_session):
    person = Person(first_name="Анна", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert "druid_tree" in out["active_oracles"]

    pool = out["pool"]
    assert len(pool) == 1
    entry = pool[0]
    assert entry["plant_slug"] == "willow"
    assert entry["plant_name_ru"] == "Ива"
    assert entry["match_count"] == 1
    assert entry["total_weight"] == 1.0
    assert len(entry["sources"]) == 1
    src = entry["sources"][0]
    assert src["oracle_id"] == "druid_tree"
    assert src["oracle_name"].startswith("Кельтский")
    assert src["role"] == "main"


def test_recommend_with_missing_birth_date(seeded_session):
    person = Person(first_name="X", birth_date="")
    out = recommend(person, seeded_session)
    assert out["pool"] == []


def test_recommend_skips_inactive_oracles(seeded_session):
    """Если druid_tree выключить (active=0) — пул должен оказаться пустым."""
    oracle = seeded_session.get(Oracle, "druid_tree")
    oracle.active = 0
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    assert "druid_tree" not in out["active_oracles"]
    assert out["pool"] == []


def test_recommend_applies_oracle_global_weight(seeded_session):
    """total_weight = сила голоса * глобальный вес оракула из БД."""
    oracle = seeded_session.get(Oracle, "druid_tree")
    oracle.weight = 0.5
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    entry = out["pool"][0]
    # запись entry weight=1.0, глобальный вес 0.5 → итог 0.5
    assert entry["total_weight"] == 0.5


def test_recommend_includes_short_story(seeded_session):
    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)
    entry = out["pool"][0]
    assert entry["plant_short_story"] is not None
    assert "Ива" in entry["plant_short_story"]
