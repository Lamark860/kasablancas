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
    assert by_id["druid_tree"]["implemented"] is True
    assert by_id["zodiac"]["implemented"] is True
    # ещё не реализованные на этапе 4
    assert by_id["druid_flower"]["implemented"] is False
    assert by_id["slavic"]["implemented"] is False
    assert by_id["druid_tree"]["required_inputs"] == ["birth_date"]
