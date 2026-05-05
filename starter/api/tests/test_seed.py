"""Сидинг oracles работает идемпотентно и подтягивает все 8 оракулов."""
from sqlalchemy import select

from vlad.models import Oracle, OracleEntry
from vlad.seed import seed_oracle_entries, seed_oracles, seed_plants


EXPECTED_ORACLE_IDS = {
    "druid_tree", "druid_flower", "zodiac", "slavic",
    "name", "eye_color", "lunar", "numerology",
}


def test_seed_oracles_first_run(db_session):
    n = seed_oracles(db_session)
    db_session.commit()
    assert n == 8
    rows = db_session.scalars(select(Oracle)).all()
    assert {r.id for r in rows} == EXPECTED_ORACLE_IDS


def test_seed_oracles_idempotent(db_session):
    seed_oracles(db_session)
    db_session.commit()
    # ручная правка — потом повторный сид не должен породить дубли
    db_session.execute(select(Oracle).where(Oracle.id == "druid_tree"))
    seed_oracles(db_session)
    db_session.commit()
    rows = db_session.scalars(select(Oracle)).all()
    assert len(rows) == 8


def test_seed_oracles_required_inputs_loaded(db_session):
    seed_oracles(db_session)
    db_session.commit()
    eye = db_session.get(Oracle, "eye_color")
    assert eye is not None
    assert eye.required_inputs == ["eye_color"]


def test_seed_entries_preserves_manual_additions(db_session):
    """Reseed по умолчанию не должен затирать ручные правки в /admin (DECISIONS.md §3)."""
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()

    # имитируем ручную правку эксперта: добавляем имя «Алина» через админку
    db_session.add(OracleEntry(
        oracle_id="name",
        matcher={"type": "name_match", "name": "Алина"},
        plant_slug="rowan",
        weight=1.0,
        role="main",
        reason_for_expert="ручная правка эксперта",
    ))
    db_session.commit()

    # повторный сид — без --prune-missing
    seed_oracle_entries(db_session, prune_missing=False)
    db_session.commit()

    rows = db_session.query(OracleEntry).filter_by(oracle_id="name").all()
    keys = {(r.matcher.get("name"), r.plant_slug) for r in rows}
    assert ("Алина", "rowan") in keys, "ручная правка должна сохраниться"


def test_seed_entries_prune_missing_removes_orphans(db_session):
    """С флагом --prune-missing записи, которых нет в JSON, удаляются."""
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()

    db_session.add(OracleEntry(
        oracle_id="name",
        matcher={"type": "name_match", "name": "Алина"},
        plant_slug="rowan",
        weight=1.0,
        role="main",
    ))
    db_session.commit()

    seed_oracle_entries(db_session, prune_missing=True)
    db_session.commit()

    rows = db_session.query(OracleEntry).filter_by(oracle_id="name").all()
    keys = {(r.matcher.get("name"), r.plant_slug) for r in rows}
    assert ("Алина", "rowan") not in keys


def test_seed_entries_idempotent_no_duplicates(db_session):
    """Двукратный сид не плодит дублей при upsert по составному ключу."""
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()
    n_before = db_session.query(OracleEntry).count()

    seed_oracle_entries(db_session)
    db_session.commit()
    n_after = db_session.query(OracleEntry).count()

    assert n_after == n_before


def test_seed_entries_updates_existing_attributes(db_session):
    """Если в JSON изменился weight/reason — upsert обновляет существующую запись."""
    seed_oracles(db_session)
    seed_plants(db_session)
    seed_oracle_entries(db_session)
    db_session.commit()

    # подменяем атрибут "вручную" — будто кто-то правил в /admin
    row = (
        db_session.query(OracleEntry)
        .filter_by(oracle_id="name", plant_slug="willow")
        .filter(OracleEntry.matcher["name"].as_string() == "Ива")
        .first()
    )
    assert row is not None
    row.weight = 0.1
    db_session.commit()

    # reseed — JSON говорит weight=1.0, должен перезатереть
    seed_oracle_entries(db_session)
    db_session.commit()

    db_session.refresh(row)
    assert row.weight == 1.0
