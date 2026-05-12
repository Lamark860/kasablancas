"""Тесты shareable публичного листа: PUT генерит share_token, GET /leaf/{token} отдаёт без auth."""
from __future__ import annotations


def _make_person(client) -> int:
    r = client.post("/persons/", json={
        "first_name": "Eva-leaf",
        "birth_date": "2000-03-05",
        "eye_color": "blue",
        "garden_zone_usda": 4,
    })
    assert r.status_code == 201
    return r.json()["id"]


def test_put_recommendation_generates_share_token(client, seeded_session):
    pid = _make_person(client)
    r = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": "willow", "expert_note": "у пруда"}],
        "title_plant_slug": "willow",
    })
    assert r.status_code == 200
    d = r.json()
    assert d["share_token"]
    # 32 байта url-safe → 43 символа
    assert 40 <= len(d["share_token"]) <= 48


def test_two_versions_get_different_tokens(client, seeded_session):
    pid = _make_person(client)
    r1 = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": "willow"}],
    })
    r2 = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": "willow"}, {"plant_slug": "apple"}],
    })
    assert r1.json()["share_token"] != r2.json()["share_token"]


def test_get_leaf_by_token_returns_recommendation(client, seeded_session):
    pid = _make_person(client)
    put_res = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": "willow", "expert_note": "share-flow"}],
        "title_plant_slug": "willow",
    }).json()
    token = put_res["share_token"]
    r = client.get(f"/leaf/{token}")
    assert r.status_code == 200
    body = r.json()
    assert body["person_id"] == pid
    assert body["title_plant_slug"] == "willow"
    assert body["curated_pool"][0]["plant_slug"] == "willow"
    assert body["share_token"] == token


def test_get_leaf_with_unknown_token_returns_404(client, seeded_session):
    r = client.get("/leaf/totally-bogus-token-xxxxxxxxxxxxxxx")
    assert r.status_code == 404


def test_old_recommendations_have_null_token(client, seeded_session):
    """Версии, созданные до этой миграции, имели share_token=None.
    Проверяем что новый GET /leaf/None не выдаёт первую попавшуюся запись.
    """
    # Создаём гостью и рекомендацию, потом ручками обнуляем токен
    pid = _make_person(client)
    put_res = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": "willow"}],
    }).json()
    # Симулируем legacy-запись — null token в БД
    from vlad.models import Recommendation
    rec = seeded_session.get(Recommendation, put_res["id"])
    rec.share_token = None
    seeded_session.commit()
    r = client.get("/leaf/null")
    assert r.status_code == 404
