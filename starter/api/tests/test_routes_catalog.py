"""API-тесты для справочников: /plants, /oracles."""


def test_list_plants(seeded_client):
    r = seeded_client.get("/plants/")
    assert r.status_code == 200
    plants = r.json()
    assert len(plants) == 22
    slugs = {p["slug"] for p in plants}
    assert {"willow", "oak", "birch", "olive", "beech"}.issubset(slugs)


def test_list_oracles_marks_implemented(seeded_client):
    r = seeded_client.get("/oracles/")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) == 8
    by_id = {o["id"]: o for o in rows}
    # реализовано (5)
    for o in ("druid_tree", "zodiac", "numerology", "eye_color", "name"):
        assert by_id[o]["implemented"] is True, o
    # отложено до расширения plants.json (3) — см. DECISIONS.md §16-18
    for o in ("druid_flower", "slavic", "lunar"):
        assert by_id[o]["implemented"] is False, o
    assert by_id["druid_tree"]["required_inputs"] == ["birth_date"]
