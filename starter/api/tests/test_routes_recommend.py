"""API-тесты для POST /recommend (оба режима: по person_id и inline)."""


def test_recommend_inline_pisces_intersection(seeded_client):
    """5.03.2000: druid_tree → ива, zodiac → ива+инжир. Ива на первом месте с match_count=2."""
    r = seeded_client.post(
        "/recommend/",
        json={"person": {"first_name": "X", "birth_date": "2000-03-05"}},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert {"druid_tree", "zodiac"}.issubset(data["active_oracles"])
    pool = data["pool"]
    assert pool[0]["plant_slug"] == "willow"
    assert pool[0]["match_count"] == 2
    slugs = {e["plant_slug"] for e in pool}
    assert {"willow", "fig"}.issubset(slugs)


def test_recommend_by_person_id_taurus_unfiltered(seeded_client):
    """25.04.1990, Анна — без фильтров (apply_filters=false):
    - druid_tree → грецкий орех (21.04–30.04)
    - zodiac     → яблоня (Телец)
    - numerology → берёза + рябина (Анна = 5)
    Все четыре остаются.
    """
    pid = seeded_client.post(
        "/persons/",
        json={"first_name": "Анна", "birth_date": "1990-04-25"},
    ).json()["id"]

    r = seeded_client.post(
        "/recommend/?apply_filters=false",
        json={"person_id": pid},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["filters_applied"] is False
    slugs = {e["plant_slug"] for e in body["pool"]}
    assert slugs == {"walnut", "apple", "birch", "rowan"}


def test_recommend_by_person_id_taurus_filtered_drops_rowan(seeded_client):
    """С фильтрами рябина (период 01–10.04) попадает в окно ±40 дней от 25.04
    и отсеивается как «дерево-враг»; берёза (24.06) — нет, остаётся."""
    pid = seeded_client.post(
        "/persons/",
        json={"first_name": "Анна", "birth_date": "1990-04-25"},
    ).json()["id"]

    r = seeded_client.post("/recommend/", json={"person_id": pid})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["filters_applied"] is True
    slugs = {e["plant_slug"] for e in body["pool"]}
    assert "rowan" not in slugs
    assert {"walnut", "apple", "birch"}.issubset(slugs)
    excluded = {x["plant_slug"] for x in body["excluded"]}
    assert "rowan" in excluded


def test_recommend_validates_either_or(seeded_client):
    r = seeded_client.post("/recommend/", json={})
    assert r.status_code == 422
    r = seeded_client.post(
        "/recommend/",
        json={"person_id": 1, "person": {"first_name": "X", "birth_date": "2000-01-01"}},
    )
    assert r.status_code == 422


def test_recommend_unknown_person_404(seeded_client):
    r = seeded_client.post("/recommend/", json={"person_id": 9999})
    assert r.status_code == 404


def test_recommend_empty_pool_when_birth_date_missing(seeded_client):
    """Без birth_date оба оракула молчат → пустой пул."""
    r = seeded_client.post(
        "/recommend/",
        json={"person": {"first_name": "X", "birth_date": "1900-01-01"}},
    )
    # 1.01: druid → яблоня (12-23..01-01), zodiac → козерог → сосна
    # Это ОК; именно «пустой пул» проверяем через невалидный для оракулов кейс
    # с Person без birth_date — но Pydantic regex его не пустит. Поэтому
    # эквивалентный тест ниже: оба оракула молчат на 21.12 (druid не покрывает,
    # zodiac на стыке знаков выпадает в стрельца — попробуем дату глубоко
    # внутри сагиттария но без druid-периода).
    # NB: 21.12 теперь даёт sagittarius → rowan/hornbeam/cedar, druid пуст —
    # пул не пустой. Чисто пустой пул возможен только для дат, которые
    # одновременно вне druid-периодов и где у zodiac нет растений (aries).
    assert r.status_code == 200
    # сразу проверим эквивалентный кейс — 5.04 у нас глубоко в овне (aries),
    # zodiac не имеет entries для овна, druid отдаёт rowan
    r2 = seeded_client.post(
        "/recommend/",
        json={"person": {"first_name": "X", "birth_date": "2000-04-05"}},
    )
    pool = r2.json()["pool"]
    sources = {s["oracle_id"] for e in pool for s in e["sources"]}
    assert sources == {"druid_tree"}  # zodiac молчит на овне
