"""Тесты POST /persons/{id}/recommendations/{rec_id}/finalize (E3)."""
from __future__ import annotations


def _make_person(client) -> int:
    r = client.post("/persons/", json={
        "first_name": "Eva-final",
        "birth_date": "2000-03-05",
        "eye_color": "blue",
        "garden_zone_usda": 4,
    })
    assert r.status_code == 201
    return r.json()["id"]


def _put_rec(client, pid: int, slug: str) -> int:
    r = client.put(f"/persons/{pid}/recommendation", json={
        "curated": [{"plant_slug": slug}],
        "title_plant_slug": slug,
    })
    assert r.status_code == 200
    return r.json()["id"]


def test_finalize_marks_one_version(client, seeded_session):
    pid = _make_person(client)
    rec_id = _put_rec(client, pid, "willow")

    # До: is_final == False
    assert client.get(f"/persons/{pid}/recommendations/{rec_id}").json()["is_final"] is False

    r = client.post(f"/persons/{pid}/recommendations/{rec_id}/finalize")
    assert r.status_code == 200
    body = r.json()
    assert body["id"] == rec_id
    assert body["is_final"] is True


def test_finalize_unmarks_previous(client, seeded_session):
    pid = _make_person(client)
    r1 = _put_rec(client, pid, "willow")
    r2 = _put_rec(client, pid, "apple")
    r3 = _put_rec(client, pid, "birch")

    # Финализируем r1
    client.post(f"/persons/{pid}/recommendations/{r1}/finalize")
    assert client.get(f"/persons/{pid}/recommendations/{r1}").json()["is_final"] is True

    # Затем финализируем r2 — r1 должна потерять флаг
    client.post(f"/persons/{pid}/recommendations/{r2}/finalize")
    assert client.get(f"/persons/{pid}/recommendations/{r1}").json()["is_final"] is False
    assert client.get(f"/persons/{pid}/recommendations/{r2}").json()["is_final"] is True
    assert client.get(f"/persons/{pid}/recommendations/{r3}").json()["is_final"] is False


def test_finalize_idempotent(client, seeded_session):
    pid = _make_person(client)
    rec_id = _put_rec(client, pid, "willow")
    client.post(f"/persons/{pid}/recommendations/{rec_id}/finalize")
    # Повторный вызов — без ошибок, флаг сохраняется
    r = client.post(f"/persons/{pid}/recommendations/{rec_id}/finalize")
    assert r.status_code == 200
    assert r.json()["is_final"] is True


def test_finalize_404_for_wrong_person(client, seeded_session):
    pid_a = _make_person(client)
    pid_b = _make_person(client)
    rec_id_a = _put_rec(client, pid_a, "willow")
    # Пытаемся финализировать запись pid_a от имени pid_b
    r = client.post(f"/persons/{pid_b}/recommendations/{rec_id_a}/finalize")
    assert r.status_code == 404


def test_list_recommendations_includes_is_final(client, seeded_session):
    pid = _make_person(client)
    rec_id = _put_rec(client, pid, "willow")
    client.post(f"/persons/{pid}/recommendations/{rec_id}/finalize")

    r = client.get(f"/persons/{pid}/recommendations")
    items = r.json()
    assert items[0]["is_final"] is True
