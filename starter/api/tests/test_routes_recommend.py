"""API-тесты для POST /recommend (оба режима: по person_id и inline)."""


def test_recommend_inline(seeded_client):
    r = seeded_client.post(
        "/recommend/",
        json={"person": {"first_name": "X", "birth_date": "2000-03-05"}},
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert "druid_tree" in data["active_oracles"]
    assert len(data["pool"]) == 1
    assert data["pool"][0]["plant_slug"] == "willow"
    assert data["pool"][0]["plant_name_ru"] == "Ива"


def test_recommend_by_person_id(seeded_client):
    pid = seeded_client.post(
        "/persons/",
        json={"first_name": "Анна", "birth_date": "1990-03-21"},  # дуб
    ).json()["id"]

    r = seeded_client.post("/recommend/", json={"person_id": pid})
    assert r.status_code == 200, r.text
    pool = r.json()["pool"]
    assert pool[0]["plant_slug"] == "oak"


def test_recommend_validates_either_or(seeded_client):
    """Должно быть указано ровно одно: person_id ИЛИ person."""
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


def test_recommend_returns_empty_pool_for_uncovered_date(seeded_client):
    """21.12 — намеренно непокрытый день в research/02."""
    r = seeded_client.post(
        "/recommend/",
        json={"person": {"first_name": "X", "birth_date": "2000-12-21"}},
    )
    assert r.status_code == 200
    assert r.json()["pool"] == []
