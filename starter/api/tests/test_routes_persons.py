"""API-тесты CRUD по /persons."""


PAYLOAD = {
    "first_name": "Анна",
    "last_name": "Иванова",
    "birth_date": "1990-03-05",
    "eye_color": "blue",
    "garden_zone_usda": 5,
}


def test_create_person(client):
    r = client.post("/persons/", json=PAYLOAD)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["id"] >= 1
    assert data["first_name"] == "Анна"
    assert data["created_at"]


def test_list_persons(client):
    client.post("/persons/", json=PAYLOAD)
    client.post("/persons/", json={**PAYLOAD, "first_name": "Борис"})
    r = client.get("/persons/")
    assert r.status_code == 200
    assert len(r.json()) == 2


def test_get_person(client):
    pid = client.post("/persons/", json=PAYLOAD).json()["id"]
    r = client.get(f"/persons/{pid}")
    assert r.status_code == 200
    assert r.json()["id"] == pid


def test_get_person_404(client):
    r = client.get("/persons/999")
    assert r.status_code == 404


def test_delete_person(client):
    pid = client.post("/persons/", json=PAYLOAD).json()["id"]
    r = client.delete(f"/persons/{pid}")
    assert r.status_code == 204
    assert client.get(f"/persons/{pid}").status_code == 404


def test_validation_birth_date_format(client):
    bad = {**PAYLOAD, "birth_date": "05.03.1990"}
    r = client.post("/persons/", json=bad)
    assert r.status_code == 422


def test_validation_eye_color_enum(client):
    bad = {**PAYLOAD, "eye_color": "purple"}
    r = client.post("/persons/", json=bad)
    assert r.status_code == 422
