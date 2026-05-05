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
    assert "zodiac" in sources_in_pool


def test_full_intersection_for_eva_pisces_blue_eyes(seeded_session):
    """Пять оракулов одновременно — главный демонстрационный кейс этапа 5.

    Ева, родилась 05.03.2000 (Рыбы, период Ивы), голубые глаза:
    - druid_tree   → ива
    - zodiac       → ива + инжир (Рыбы)
    - numerology   → дуб (Ева=1 по Пифагору)
    - eye_color    → ива (голубые)
    - name         → яблоня (Ева — «жизнь» / древо познания)

    Архитектурный «сырой» пул — без фильтров. Дуб попал бы в «дерево-враг»
    (период 21.03 в окне ±40 дней от 05.03), это проверяется отдельно.
    """
    person = Person(
        first_name="Ева",
        birth_date="2000-03-05",
        eye_color="blue",
    )
    out = recommend(person, seeded_session, apply_filters_flag=False)

    pool = out["pool"]
    by_slug = {e["plant_slug"]: e for e in pool}

    assert by_slug["willow"]["match_count"] == 3
    willow_sources = {s["oracle_id"] for s in by_slug["willow"]["sources"]}
    assert willow_sources == {"druid_tree", "zodiac", "eye_color"}

    assert "apple" in by_slug
    assert "oak" in by_slug
    assert "fig" in by_slug

    assert pool[0]["plant_slug"] == "willow"
    assert out["filters_applied"] is False
    assert out["excluded"] == []


def test_eva_with_filters_drops_enemy_oak(seeded_session):
    """С фильтрами для Евы 05.03 дуб (21.03) выпадает как «дерево-враг»."""
    person = Person(first_name="Ева", birth_date="2000-03-05", eye_color="blue")
    out = recommend(person, seeded_session, apply_filters_flag=True)

    slugs = {e["plant_slug"] for e in out["pool"]}
    assert "willow" in slugs
    assert "oak" not in slugs

    excluded_slugs = {x["plant_slug"] for x in out["excluded"]}
    assert "oak" in excluded_slugs
    oak_reason = next(x["reason"] for x in out["excluded"] if x["plant_slug"] == "oak")
    assert "враг" in oak_reason
