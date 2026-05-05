"""Куратор-режим эксперта: PUT/GET /persons/{id}/recommendation + PDF /reports.

Тесты гоняют пайплайн end-to-end на seeded_client: создаём Person, считаем
оркестратор, сохраняем кураторский выбор, проверяем что повторный PUT
не плодит новые строки и что PDF возвращается с magic-байтами %PDF.
"""
from __future__ import annotations


PAYLOAD_EVA = {
    "first_name": "Ева",
    "birth_date": "2000-03-05",
    "eye_color": "blue",
    "garden_zone_usda": 4,
}


def _create_eva(client):
    r = client.post("/persons/", json=PAYLOAD_EVA)
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_save_recommendation_creates_row(seeded_client):
    pid = _create_eva(seeded_client)

    r = seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={
            "curated_slugs": ["willow", "apple"],
            "title_plant_slug": "willow",
            "expert_notes": "вокруг ивы — водные акценты, без розовых кустов",
            "apply_filters": True,
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()

    assert body["person_id"] == pid
    # curated_pool теперь list[{plant_slug, expert_note}] — обратная совместимость через curated_slugs
    assert [it["plant_slug"] for it in body["curated_pool"]] == ["willow", "apple"]
    assert all(it["expert_note"] is None for it in body["curated_pool"])
    assert body["title_plant_slug"] == "willow"
    assert body["expert_notes"].startswith("вокруг ивы")
    assert body["raw_pool"][0]["plant_slug"] == "willow"
    assert "druid_tree" in body["active_oracles"]
    assert body["input_snapshot"]["birth_date"] == "2000-03-05"
    assert body["input_snapshot"]["eye_color"] == "blue"


def test_save_recommendation_with_per_plant_notes(seeded_client):
    """Новый формат: curated с per-plant заметками эксперта (D9)."""
    pid = _create_eva(seeded_client)
    r = seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={
            "curated": [
                {"plant_slug": "willow", "expert_note": "ставить ближе к воде, не на холм"},
                {"plant_slug": "apple", "expert_note": "карликовый сорт"},
                {"plant_slug": "birch", "expert_note": None},
            ],
            "title_plant_slug": "willow",
            "expert_notes": "общая палитра — холодная сторона участка",
        },
    )
    assert r.status_code == 200, r.text
    pool = r.json()["curated_pool"]
    assert pool[0] == {"plant_slug": "willow", "expert_note": "ставить ближе к воде, не на холм"}
    assert pool[1] == {"plant_slug": "apple", "expert_note": "карликовый сорт"}
    assert pool[2] == {"plant_slug": "birch", "expert_note": None}


def test_save_recommendation_creates_new_version(seeded_client):
    """D8: повторный PUT плодит новую версию в истории, не обновляет старую."""
    pid = _create_eva(seeded_client)

    r1 = seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow"], "title_plant_slug": "willow"},
    )
    rec_id_1 = r1.json()["id"]

    r2 = seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow", "apple"], "title_plant_slug": "willow"},
    )
    rec_id_2 = r2.json()["id"]

    assert rec_id_1 != rec_id_2, "PUT должен плодить новую версию"
    assert rec_id_2 > rec_id_1

    # GET /recommendation возвращает последнюю
    last = seeded_client.get(f"/persons/{pid}/recommendation").json()
    assert last["id"] == rec_id_2
    assert [it["plant_slug"] for it in last["curated_pool"]] == ["willow", "apple"]


def test_list_recommendations_returns_history(seeded_client):
    """GET /persons/{id}/recommendations — список версий, новейшая первая."""
    pid = _create_eva(seeded_client)
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow"], "title_plant_slug": "willow"},
    )
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow", "apple"], "title_plant_slug": "willow"},
    )
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow", "apple", "birch"], "title_plant_slug": "willow"},
    )

    r = seeded_client.get(f"/persons/{pid}/recommendations")
    assert r.status_code == 200
    versions = r.json()
    assert len(versions) == 3
    # новейшая первая
    assert versions[0]["id"] > versions[1]["id"] > versions[2]["id"]
    # содержат curated_pool, не содержат raw_pool
    assert "curated_pool" in versions[0]
    assert "raw_pool" not in versions[0]
    # в новейшей — три растения
    assert len(versions[0]["curated_pool"]) == 3


def test_list_recommendations_empty_for_person_without_history(seeded_client):
    pid = _create_eva(seeded_client)
    r = seeded_client.get(f"/persons/{pid}/recommendations")
    assert r.status_code == 200
    assert r.json() == []


def test_list_recommendations_404_for_unknown_person(seeded_client):
    assert seeded_client.get("/persons/99999/recommendations").status_code == 404


def test_get_specific_recommendation_version(seeded_client):
    """GET /persons/{id}/recommendations/{rec_id} — конкретная версия из истории."""
    pid = _create_eva(seeded_client)
    r1 = seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow"], "title_plant_slug": "willow"},
    )
    seeded_client.put(  # вторая версия
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["apple"], "title_plant_slug": "apple"},
    )
    old_id = r1.json()["id"]

    # старую версию можно достать
    r = seeded_client.get(f"/persons/{pid}/recommendations/{old_id}")
    assert r.status_code == 200
    assert r.json()["id"] == old_id
    assert [it["plant_slug"] for it in r.json()["curated_pool"]] == ["willow"]

    # чужой rec_id — 404
    assert seeded_client.get(f"/persons/{pid}/recommendations/99999").status_code == 404


def test_get_recommendation_404_until_saved(seeded_client):
    pid = _create_eva(seeded_client)
    assert seeded_client.get(f"/persons/{pid}/recommendation").status_code == 404
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={"curated_slugs": ["willow"], "title_plant_slug": "willow"},
    )
    assert seeded_client.get(f"/persons/{pid}/recommendation").status_code == 200


def test_get_recommendation_404_for_unknown_person(seeded_client):
    assert seeded_client.get("/persons/99999/recommendation").status_code == 404


def test_pdf_404_until_saved(seeded_client):
    pid = _create_eva(seeded_client)
    r = seeded_client.get(f"/reports/{pid}.pdf")
    assert r.status_code == 404, r.text


def test_pdf_renders_after_save(seeded_client):
    pid = _create_eva(seeded_client)
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={
            "curated_slugs": ["willow", "apple"],
            "title_plant_slug": "willow",
            "expert_notes": "тестовая заметка",
        },
    )

    r = seeded_client.get(f"/reports/{pid}.pdf")
    assert r.status_code == 200, r.text
    assert r.headers["content-type"] == "application/pdf"
    assert r.content.startswith(b"%PDF"), "ответ должен быть валидным PDF"
    # минимум вменяемого размера — однопиксельный stub меньше нескольких КБ
    assert len(r.content) > 4_000, f"подозрительно маленький PDF: {len(r.content)} bytes"


def test_pdf_with_per_plant_notes_renders(seeded_client):
    """PDF с заметками на конкретные растения — рендерится (D9)."""
    pid = _create_eva(seeded_client)
    seeded_client.put(
        f"/persons/{pid}/recommendation",
        json={
            "curated": [
                {"plant_slug": "willow", "expert_note": "ставить у пруда"},
                {"plant_slug": "apple", "expert_note": "карликовый сорт"},
            ],
            "title_plant_slug": "willow",
        },
    )
    r = seeded_client.get(f"/reports/{pid}.pdf")
    assert r.status_code == 200
    assert r.content.startswith(b"%PDF")


def test_normalize_curated_handles_legacy_string_format():
    """В БД могут лежать старые записи curated_pool=list[str] — нормализуем."""
    from vlad.pdf import _normalize_curated
    legacy = ["willow", "apple"]
    assert _normalize_curated(legacy) == [
        {"plant_slug": "willow", "expert_note": None},
        {"plant_slug": "apple", "expert_note": None},
    ]
    new_format = [{"plant_slug": "willow", "expert_note": "у пруда"}]
    assert _normalize_curated(new_format) == [
        {"plant_slug": "willow", "expert_note": "у пруда"},
    ]
    mixed = ["willow", {"plant_slug": "apple", "expert_note": "карликовый"}]
    assert _normalize_curated(mixed) == [
        {"plant_slug": "willow", "expert_note": None},
        {"plant_slug": "apple", "expert_note": "карликовый"},
    ]
