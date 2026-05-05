"""Тесты vlad.dump_seed: round-trip dump → reseed даёт тот же набор данных."""
from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from vlad.dump_seed import dump_all
from vlad.main import app
from vlad.models import OracleEntry, Plant
from vlad.seed import seed_oracle_entries, seed_oracles, seed_plants


client = TestClient(app)


def test_dump_writes_expected_files(tmp_path: Path, seeded_session):
    counts = dump_all(seeded_session, target_dir=tmp_path)
    assert (tmp_path / "plants.json").exists()
    assert (tmp_path / "oracles.json").exists()
    # хотя бы один из реализованных оракулов
    assert (tmp_path / "druid-tree.json").exists()
    assert counts["plants.json"] == 22
    assert counts["oracles.json"] == 8


def test_dump_round_trip_preserves_data(tmp_path: Path, db_session):
    """Засеваем, дампим, очищаем БД, заново сидим из дампа — содержимое то же."""
    # засев из реальных JSON
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()

    plant_count_before = db_session.query(Plant).count()
    entry_count_before = db_session.query(OracleEntry).count()
    sample_entry = (
        db_session.query(OracleEntry)
        .filter_by(oracle_id="name", plant_slug="willow")
        .filter(OracleEntry.matcher["name"].as_string() == "Ива")
        .one()
    )
    sample_weight_before = sample_entry.weight

    # dump в tmp_path
    dump_all(db_session, target_dir=tmp_path)

    # Ручная правка: меняем weight, чтобы убедиться что reseed из дампа его перезатрёт обратно
    sample_entry.weight = 0.001
    db_session.commit()

    # Сидим обратно из дампа — нужно подменить SEED_DIR для seed_*
    import vlad.seed as seed_mod
    original_dir = seed_mod.SEED_DIR
    seed_mod.SEED_DIR = tmp_path
    try:
        seed_oracle_entries(db_session)
        db_session.commit()
    finally:
        seed_mod.SEED_DIR = original_dir

    db_session.refresh(sample_entry)
    assert sample_entry.weight == sample_weight_before
    assert db_session.query(Plant).count() == plant_count_before
    assert db_session.query(OracleEntry).count() == entry_count_before


def test_dump_skips_oracles_without_entries(tmp_path: Path, seeded_session):
    """Для оракулов, у которых записей нет (slavic, lunar, druid_flower), файл не создаётся."""
    dump_all(seeded_session, target_dir=tmp_path)
    assert not (tmp_path / "slavic.json").exists()
    assert not (tmp_path / "lunar.json").exists()
    assert not (tmp_path / "druid-flower.json").exists()


def test_dump_strips_null_fields(tmp_path: Path, seeded_session):
    dump_all(seeded_session, target_dir=tmp_path)
    plants = json.loads((tmp_path / "plants.json").read_text())
    # ни в одном растении не должно быть ключей с null значением
    for p in plants:
        for k, v in p.items():
            assert v is not None, f"{p['slug']}.{k} равен None — должно быть опущено"


def test_seed_dump_view_get_renders_button():
    r = client.get("/admin/seed-dump")
    assert r.status_code == 200
    assert "Выгрузить сейчас" in r.text


def test_seed_dump_view_post_writes_files(tmp_path: Path, monkeypatch):
    # подменяем SEED_DIR чтобы не трогать реальные сиды
    import vlad.dump_seed as dump_mod
    monkeypatch.setattr(dump_mod, "SEED_DIR", tmp_path)
    # admin импортировал SEED_DIR в модуль — патчим и там
    import vlad.admin as admin_mod
    monkeypatch.setattr(admin_mod, "SEED_DIR", tmp_path)
    # dump_all использует default-arg SEED_DIR = dump_mod.SEED_DIR на момент вызова функции,
    # но default уже захвачен при определении. Переопределим саму функцию через wrapper:
    original_dump_all = dump_mod.dump_all
    monkeypatch.setattr(
        admin_mod, "dump_all",
        lambda session, target_dir=tmp_path: original_dump_all(session, target_dir=target_dir),
    )

    r = client.post("/admin/seed-dump")
    assert r.status_code == 200
    assert "Готово" in r.text
    assert (tmp_path / "plants.json").exists()
    assert (tmp_path / "oracles.json").exists()
