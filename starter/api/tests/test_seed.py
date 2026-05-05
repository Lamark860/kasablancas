"""Сидинг oracles работает идемпотентно и подтягивает все 8 оракулов."""
from sqlalchemy import select

from vlad.models import Oracle
from vlad.seed import seed_oracles


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
