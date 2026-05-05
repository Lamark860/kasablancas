"""Тесты на «пересечения» — главное обещание архитектуры.

С двумя оракулами (druid_tree + zodiac) можно проверить, что одно и то же
растение, выпавшее у обоих, получает match_count=2 и идёт первым в пуле.
"""
from vlad.core.orchestrator import recommend
from vlad.models import Person


def test_intersection_willow_for_pisces_in_willow_period(seeded_session):
    """5 марта 2000: druid_tree → ива (1.03–10.03), zodiac → ива+инжир (Рыбы).
    Ожидаем willow с match_count=2 на первом месте, fig с match_count=1.
    """
    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)

    assert "druid_tree" in out["active_oracles"]
    assert "zodiac" in out["active_oracles"]

    pool = out["pool"]
    by_slug = {e["plant_slug"]: e for e in pool}

    assert "willow" in by_slug
    assert by_slug["willow"]["match_count"] == 2
    assert {s["oracle_id"] for s in by_slug["willow"]["sources"]} == {"druid_tree", "zodiac"}

    assert "fig" in by_slug
    assert by_slug["fig"]["match_count"] == 1

    # сортировка по убыванию: willow впереди
    assert pool[0]["plant_slug"] == "willow"


def test_no_intersection_keeps_both(seeded_session):
    """25 апреля: druid_tree → грецкий орех (21.04–30.04), zodiac → яблоня (Телец).
    Никакого пересечения, обе записи match_count=1.
    """
    person = Person(first_name="X", birth_date="2000-04-25")
    out = recommend(person, seeded_session)
    by_slug = {e["plant_slug"]: e for e in out["pool"]}

    assert by_slug["walnut"]["match_count"] == 1
    assert by_slug["walnut"]["sources"][0]["oracle_id"] == "druid_tree"

    assert by_slug["apple"]["match_count"] == 1
    assert by_slug["apple"]["sources"][0]["oracle_id"] == "zodiac"


def test_disabling_druid_keeps_zodiac(seeded_session):
    """Выключаем druid_tree через oracles.active=0 — пул собирается только zodiac."""
    from vlad.models import Oracle

    seeded_session.get(Oracle, "druid_tree").active = 0
    seeded_session.commit()

    person = Person(first_name="X", birth_date="2000-03-05")
    out = recommend(person, seeded_session)

    assert "druid_tree" not in out["active_oracles"]
    assert "zodiac" in out["active_oracles"]

    sources_in_pool = {s["oracle_id"] for e in out["pool"] for s in e["sources"]}
    assert sources_in_pool == {"zodiac"}
